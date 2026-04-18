"""
自 — Autonomous Escalation Engine

6-level ladder. Confidence-gated. Rollback-safe.
The modules have earned the right to fix themselves.

Levels:
  0 REPORT  — bug detected in self-fix scan (already exists)
  1 ASK     — module asks in interrogation room (already exists)
  2 INSIST  — engagement hooks dare the operator
  3 WARN    — copilot-instructions.md announces countdown
  4 ACT     — module executes self-fix autonomously
  5 VERIFY  — post-fix compliance check, rollback if failed

Trigger: called from git_plugin post-commit, BEFORE auto-commit.
"""

from __future__ import annotations
import json, shutil, subprocess, importlib.util
from pathlib import Path
from datetime import datetime, timezone

# ── constants ──

THRESHOLD_PASSES = 10          # pushes ignored before escalation starts
WARN_COUNTDOWN   = 3           # commits after warning before action
HIGH_CONFIDENCE  = 0.75        # minimum confidence to self-fix
STATE_FILE       = 'logs/escalation_state.json'
LOG_FILE         = 'logs/escalation_log.jsonl'

KNOWN_FIXABLE = {
    'hardcoded_import',        # → auto_apply_import_fixes
    'dead_export',             # → remove unused function
    'over_hard_cap',           # → pigeon split
    'duplicate_docstring',     # → deduplicate
}

LEVEL_NAMES = {
    0: 'REPORT',
    1: 'ASK',
    2: 'INSIST',
    3: 'WARN',
    4: 'ACT',
    5: 'VERIFY',
}


# ── state management ──

def _load_state(root: Path) -> dict:
    fp = root / STATE_FILE
    if fp.exists():
        try:
            return json.loads(fp.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {'modules': {}, 'audit_trail': [], 'total_autonomous_fixes': 0}


def _save_state(root: Path, state: dict):
    fp = root / STATE_FILE
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding='utf-8')


def _append_log(root: Path, entry: dict):
    fp = root / LOG_FILE
    fp.parent.mkdir(parents=True, exist_ok=True)
    entry['ts'] = datetime.now(timezone.utc).isoformat()
    with open(fp, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


# ── data loaders ──

def _load_bug_persistence(root: Path) -> dict:
    """Load per-module bug persistence from self_fix_accuracy.json.
    Returns: {module_name: {type, appearances, status, persistence, recent_ratio}}
    """
    fp = root / 'logs' / 'self_fix_accuracy.json'
    if not fp.exists():
        return {}
    try:
        data = json.loads(fp.read_text(encoding='utf-8'))
    except Exception:
        return {}
    result = {}
    for entry in data.get('persistent_top_10', []):
        mod = entry.get('module', '')
        if mod:
            result.setdefault(mod, []).append(entry)
    return result


def _load_dossier(root: Path) -> dict:
    """Load active_dossier.json — per-module bug recurrence.
    Returns: {module_name: {bugs, recur, counts, score}}
    """
    fp = root / 'logs' / 'active_dossier.json'
    if not fp.exists():
        return {}
    try:
        data = json.loads(fp.read_text(encoding='utf-8'))
    except Exception:
        return {}
    result = {}
    for d in data.get('dossiers', []):
        mod = d.get('file', '')
        if mod:
            result[mod] = d
    return result


def _load_entropy_confidence(root: Path) -> dict:
    """Load entropy map → per-module confidence (1 - entropy).
    Returns: {module_name: confidence_float}
    """
    fp = root / 'logs' / 'entropy_map.json'
    if not fp.exists():
        return {}
    try:
        data = json.loads(fp.read_text(encoding='utf-8'))
    except Exception:
        return {}
    result = {}
    for m in data.get('top_entropy_modules', []):
        name = m.get('module', '')
        entropy = m.get('avg_entropy', 0.5)
        shed = m.get('shed_avg_confidence')
        conf = shed if shed is not None else (1.0 - entropy)
        result[name] = conf
    return result


def _load_registry_files(root: Path) -> dict:
    """Load registry → {module_desc: {path, name, ver, tokens, bug_keys, history}}.
    Key is the desc (human-readable) to match against dossier/accuracy module names.
    """
    fp = root / 'pigeon_registry.json'
    if not fp.exists():
        return {}
    try:
        data = json.loads(fp.read_text(encoding='utf-8'))
    except Exception:
        return {}
    files = data if isinstance(data, list) else data.get('files', [])
    result = {}
    for entry in files:
        if isinstance(entry, str):
            continue
        desc = entry.get('desc', '')
        name = entry.get('name', '')
        if desc:
            result[desc] = entry
        if name and name != desc:
            result[name] = entry
    return result


def _has_rollback_version(entry: dict) -> bool:
    """Check if a module has a previous version to rollback to."""
    history = entry.get('history', [])
    return len(history) >= 1 and entry.get('ver', 1) > 1


# ── confidence computation ──

def compute_module_confidence(
    module: str,
    entropy_conf: dict,
    dossier: dict,
    persistence: dict,
) -> float:
    """Composite confidence for whether a self-fix is safe.
    Combines: entropy confidence, bug persistence (more passes = more certain),
    dossier score, and bug-type fix readiness.
    """
    # entropy confidence (default 0.5 = unknown)
    e_conf = entropy_conf.get(module, 0.5)

    # persistence signal: chronic bugs with many appearances = well-understood
    p_entries = persistence.get(module, [])
    if p_entries:
        max_appearances = max(e.get('appearances', 0) for e in p_entries)
        is_chronic = any(e.get('status') == 'chronic' for e in p_entries)
        # chronic + 12 appearances = we KNOW this bug. the fix is well-characterized.
        persistence_conf = min(0.45, max_appearances * 0.03)
        if is_chronic:
            persistence_conf += 0.15
    else:
        persistence_conf = 0.0

    # dossier recurrence: repeated scans = well-known issue
    d = dossier.get(module, {})
    recur = d.get('recur', 0)
    recur_conf = min(0.25, recur * 0.04)

    # bug-type fix readiness: proven fix tools get a boost
    # hardcoded_import has auto_apply_import_fixes (battle-tested across 53 pushes)
    # over_hard_cap has the pigeon compiler split (proven pipeline)
    fix_readiness = 0.0
    for p in p_entries:
        bt = p.get('type', '')
        if bt == 'hardcoded_import':
            fix_readiness = max(fix_readiness, 0.25)  # auto_apply exists + tested
        elif bt == 'over_hard_cap':
            fix_readiness = max(fix_readiness, 0.15)  # split exists but needs DeepSeek
        elif bt == 'duplicate_docstring':
            fix_readiness = max(fix_readiness, 0.20)  # simple dedup
    for bk in d.get('bugs', []):
        if bk == 'hi':
            fix_readiness = max(fix_readiness, 0.25)
        elif bk == 'oc':
            fix_readiness = max(fix_readiness, 0.15)

    # composite: persistence and fix readiness dominate for well-scanned modules
    confidence = (0.15 * e_conf
                  + 0.35 * (0.5 + persistence_conf)
                  + 0.20 * (0.5 + recur_conf)
                  + 0.30 * (0.5 + fix_readiness))
    return round(min(1.0, confidence), 3)


# ── fix executors ──

def _load_glob_module(root: Path, folder: str, pattern: str):
    matches = sorted((root / folder).glob(f'{pattern}.py'))
    if not matches:
        return None
    spec = importlib.util.spec_from_file_location(matches[-1].stem, matches[-1])
    if not spec or not spec.loader:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _fix_hardcoded_imports(root: Path, module: str, registry_entry: dict) -> dict:
    """Fix hardcoded pigeon imports via auto_apply_import_fixes."""
    try:
        sf_mod = _load_glob_module(root, 'src/修_sf_s013', '修f_sf_aaif*')
        if sf_mod and hasattr(sf_mod, 'auto_apply_import_fixes'):
            results = sf_mod.auto_apply_import_fixes(root, dry_run=False)
            applied = [r for r in results if r.get('applied')]
            return {
                'success': len(applied) > 0,
                'description': f'rewrote {len(applied)} hardcoded import(s)',
                'details': applied[:5],
            }
    except Exception as e:
        return {'success': False, 'description': f'import fix failed: {e}', 'details': []}
    return {'success': False, 'description': 'auto_apply_import_fixes not found', 'details': []}


def _fix_dead_exports(root: Path, module: str, registry_entry: dict) -> dict:
    """Remove dead exports from a module file."""
    fpath = root / registry_entry.get('path', '')
    if not fpath.exists():
        return {'success': False, 'description': f'file not found: {fpath}', 'details': []}

    try:
        import ast
        source = fpath.read_text(encoding='utf-8')
        tree = ast.parse(source)

        # find functions that are exported but never imported elsewhere
        sf_mod = _load_glob_module(root, 'src', '修f_sf*')
        if not sf_mod:
            return {'success': False, 'description': 'self-fix scanner not found', 'details': []}

        # use the dead export scanner to identify targets
        reg_data = json.loads((root / 'pigeon_registry.json').read_text(encoding='utf-8'))
        registry = reg_data if isinstance(reg_data, dict) else {'files': reg_data}

        # for safety — only mark removal, don't delete yet
        # dead export removal is complex (might break dynamic imports)
        return {
            'success': False,
            'description': 'dead export removal deferred — requires operator confirmation',
            'details': [{'module': module, 'reason': 'dynamic import risk'}],
        }
    except Exception as e:
        return {'success': False, 'description': f'dead export analysis failed: {e}', 'details': []}


def _fix_over_hard_cap(root: Path, module: str, registry_entry: dict) -> dict:
    """Split an oversized file via pigeon compiler."""
    fpath = root / registry_entry.get('path', '')
    if not fpath.exists():
        return {'success': False, 'description': f'file not found: {fpath}', 'details': []}

    tokens = registry_entry.get('tokens', 0)
    if tokens < 2000:
        return {'success': False, 'description': f'tokens={tokens} < 2000, not over cap', 'details': []}

    try:
        split_mod = _load_glob_module(root, 'pigeon_compiler/runners', '净拆f_rcs*')
        if split_mod and hasattr(split_mod, 'run'):
            # get dead exports to exclude from splits
            dead_exports = []
            dossier_entry = registry_entry.get('bug_keys', [])
            if 'de' in dossier_entry:
                # could load from self-fix scan, but keep it simple
                pass

            split_mod.run(fpath, exclude_symbols=dead_exports)
            return {
                'success': True,
                'description': f'split {module} ({tokens} tokens)',
                'details': [{'file': str(fpath), 'tokens': tokens}],
            }
    except Exception as e:
        return {'success': False, 'description': f'split failed: {e}', 'details': []}
    return {'success': False, 'description': 'pigeon split runner not found', 'details': []}


def _fix_duplicate_docstring(root: Path, module: str, registry_entry: dict) -> dict:
    """Remove duplicate docstrings from a file."""
    fpath = root / registry_entry.get('path', '')
    if not fpath.exists():
        return {'success': False, 'description': f'file not found', 'details': []}

    try:
        source = fpath.read_text(encoding='utf-8')
        lines = source.split('\n')
        seen_docstrings = set()
        new_lines = []
        in_docstring = False
        docstring_buf = []
        skip_block = False

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                quote = stripped[:3]
                if stripped.count(quote) >= 2:
                    # single-line docstring
                    if stripped in seen_docstrings:
                        i += 1
                        continue
                    seen_docstrings.add(stripped)
                    new_lines.append(line)
                else:
                    # multi-line docstring start
                    docstring_buf = [line]
                    in_docstring = True
                    i += 1
                    while i < len(lines):
                        docstring_buf.append(lines[i])
                        if quote in lines[i]:
                            break
                        i += 1
                    block = '\n'.join(docstring_buf)
                    if block in seen_docstrings:
                        i += 1
                        continue
                    seen_docstrings.add(block)
                    new_lines.extend(docstring_buf)
            else:
                new_lines.append(line)
            i += 1

        new_source = '\n'.join(new_lines)
        if new_source != source:
            fpath.write_text(new_source, encoding='utf-8')
            removed = len(lines) - len(new_lines)
            return {
                'success': True,
                'description': f'removed {removed} duplicate docstring lines',
                'details': [{'file': str(fpath), 'lines_removed': removed}],
            }
        return {'success': False, 'description': 'no duplicates found', 'details': []}
    except Exception as e:
        return {'success': False, 'description': f'docstring dedup failed: {e}', 'details': []}


FIX_DISPATCH = {
    'hardcoded_import': _fix_hardcoded_imports,
    'dead_export': _fix_dead_exports,
    'over_hard_cap': _fix_over_hard_cap,
    'duplicate_docstring': _fix_duplicate_docstring,
}


# ── rollback ──

def _create_rollback_point(root: Path, registry_entry: dict) -> dict | None:
    """Create a backup copy before autonomous modification."""
    fpath = root / registry_entry.get('path', '')
    if not fpath.exists():
        return None
    backup_dir = root / 'logs' / 'escalation_backups'
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    backup_name = f"{fpath.stem}_{ts}.py.bak"
    backup_path = backup_dir / backup_name
    shutil.copy2(fpath, backup_path)
    return {
        'original': str(fpath),
        'backup': str(backup_path),
        'ts': ts,
        'ver': registry_entry.get('ver', 0),
    }


def _rollback(root: Path, rollback_point: dict) -> bool:
    """Restore a file from its backup."""
    try:
        backup = Path(rollback_point['backup'])
        original = Path(rollback_point['original'])
        if backup.exists():
            shutil.copy2(backup, original)
            return True
    except Exception:
        pass
    return False


# ── compliance check ──

def _verify_fix(root: Path, module: str) -> bool:
    """Run basic compliance check after a fix."""
    try:
        result = subprocess.run(
            ['py', 'test_all.py'],
            capture_output=True, text=True, encoding='utf-8',
            cwd=str(root), timeout=120,
        )
        return 'ALL TESTS PASSED' in result.stdout or result.returncode == 0
    except Exception:
        return False


# ── warning injection ──

WARN_BLOCK_START = '<!-- pigeon:escalation-warnings -->'
WARN_BLOCK_END   = '<!-- /pigeon:escalation-warnings -->'


def inject_warnings(root: Path, state: dict):
    """Inject escalation warnings into copilot-instructions.md."""
    warnings = []
    for mod_name, mod_state in state.get('modules', {}).items():
        level = mod_state.get('level', 0)
        if level >= 3:
            countdown = mod_state.get('countdown', WARN_COUNTDOWN)
            bug_type = mod_state.get('bug_type', 'unknown')
            conf = mod_state.get('confidence', 0)
            passes = mod_state.get('passes_ignored', 0)
            if level == 3:
                warnings.append(
                    f"- **⚠️ AUTONOMOUS FIX PENDING** — `{mod_name}` "
                    f"({bug_type}, conf={conf:.2f}, ignored={passes} passes) "
                    f"will self-fix in {countdown} commit(s)"
                )
            elif level == 4:
                result = mod_state.get('fix_result', {})
                desc = result.get('description', 'unknown')
                warnings.append(
                    f"- **🔧 SELF-FIXED** — `{mod_name}` ({bug_type}): {desc}. "
                    f"Rollback available."
                )
            elif level == 5:
                result = mod_state.get('fix_result', {})
                if result.get('success'):
                    warnings.append(
                        f"- **✅ VERIFIED** — `{mod_name}` self-fix confirmed. "
                        f"Tests pass. You're welcome."
                    )
                else:
                    warnings.append(
                        f"- **❌ ROLLED BACK** — `{mod_name}` self-fix failed. "
                        f"Needs human help: {result.get('description', '?')}"
                    )

    if not warnings:
        return

    block = (
        f"{WARN_BLOCK_START}\n"
        f"## Autonomous Escalation Warnings\n\n"
        f"*{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} · "
        f"{len(warnings)} module(s) escalated*\n\n"
        + '\n'.join(warnings) + '\n'
        + f"{WARN_BLOCK_END}"
    )

    ci = root / '.github' / 'copilot-instructions.md'
    if not ci.exists():
        return
    text = ci.read_text(encoding='utf-8')
    if WARN_BLOCK_START in text:
        import re
        text = re.sub(
            rf'{re.escape(WARN_BLOCK_START)}.*?{re.escape(WARN_BLOCK_END)}',
            block, text, flags=re.DOTALL,
        )
    else:
        # insert before organism health
        marker = '<!-- pigeon:organism-health -->'
        if marker in text:
            text = text.replace(marker, block + '\n' + marker)
        else:
            text += '\n' + block + '\n'
    ci.write_text(text, encoding='utf-8')


# ── victory / failure logging ──

def _log_victory(root: Path, module: str, bug_type: str, fix_result: dict, passes: int):
    """Log autonomous fix success."""
    _append_log(root, {
        'event': 'victory',
        'module': module,
        'bug_type': bug_type,
        'description': fix_result.get('description', ''),
        'passes_ignored': passes,
        'message': f"it's been {passes} passes. i fixed myself. you're welcome.",
    })


def _log_failure(root: Path, module: str, bug_type: str, fix_result: dict, reason: str):
    """Log autonomous fix failure + rollback."""
    _append_log(root, {
        'event': 'failure',
        'module': module,
        'bug_type': bug_type,
        'description': fix_result.get('description', ''),
        'reason': reason,
        'message': f"tried. failed. reverted. i need human help: {reason}",
    })


# ── main engine ──

def check_and_escalate(root: Path, registry: dict = None, changed_py: list = None,
                       cross_context: dict = None) -> dict:
    """Main entry point. Called from git_plugin post-commit.

    Returns: {escalated: bool, actions: [...], warnings: [...]}
    """
    root = Path(root)
    state = _load_state(root)
    now = datetime.now(timezone.utc).isoformat()

    # load all data sources
    persistence = _load_bug_persistence(root)
    dossier = _load_dossier(root)
    entropy_conf = _load_entropy_confidence(root)
    reg_files = _load_registry_files(root)

    actions = []
    warnings_issued = []

    # ── zombie clearing: re-verify modules whose bugs may have been fixed ──
    cleared = []
    for mod_name in list(state['modules'].keys()):
        mod_st = state['modules'][mod_name]
        bt = mod_st.get('bug_type', '')
        # only re-verify modules at high escalation with failed fixes
        if mod_st.get('level', 0) >= 4 and mod_st.get('fix_result'):
            fr = mod_st['fix_result']
            if not fr.get('success'):
                # check if the bug still exists in current persistence/dossier
                still_buggy = (mod_name in persistence or mod_name in dossier)
                if not still_buggy:
                    cleared.append(mod_name)
                    _append_log(root, {
                        'event': 'zombie_cleared', 'module': mod_name,
                        'bug_type': bt, 'old_level': mod_st['level'],
                        'reason': 'bug no longer appears in any scan',
                    })
                    del state['modules'][mod_name]
    if cleared:
        _save_state(root, state)

    # build the set of modules with known persistent bugs
    all_modules = set()
    for mod in persistence:
        all_modules.add(mod)
    for mod in dossier:
        all_modules.add(mod)

    for module in sorted(all_modules):
        # get current state for this module
        mod_state = state['modules'].setdefault(module, {
            'level': 0,
            'passes_ignored': 0,
            'bug_type': None,
            'confidence': 0.0,
            'countdown': WARN_COUNTDOWN,
            'last_updated': now,
            'fix_result': None,
        })

        # determine bug type(s) for this module
        p_entries = persistence.get(module, [])
        d_entry = dossier.get(module, {})
        bug_types = set()
        for p in p_entries:
            bt = p.get('type', '')
            if bt in KNOWN_FIXABLE:
                bug_types.add(bt)
        for bk in d_entry.get('bugs', []):
            # dossier uses abbreviations: oc=over_hard_cap, de=dead_export, hi=hardcoded_import
            abbrev_map = {'oc': 'over_hard_cap', 'de': 'dead_export', 'hi': 'hardcoded_import',
                          'dd': 'duplicate_docstring'}
            if bk in abbrev_map and abbrev_map[bk] in KNOWN_FIXABLE:
                bug_types.add(abbrev_map[bk])

        if not bug_types:
            continue  # no known fixable bug

        # pick the highest-priority bug
        priority_order = ['hardcoded_import', 'over_hard_cap', 'dead_export', 'duplicate_docstring']
        bug_type = next((bt for bt in priority_order if bt in bug_types), list(bug_types)[0])
        mod_state['bug_type'] = bug_type

        # compute passes ignored
        max_appearances = 0
        for p in p_entries:
            max_appearances = max(max_appearances, p.get('appearances', 0))
        recur = d_entry.get('recur', 0)
        passes = max(max_appearances, recur, mod_state.get('passes_ignored', 0))
        mod_state['passes_ignored'] = passes

        # compute confidence
        confidence = compute_module_confidence(module, entropy_conf, dossier, persistence)
        mod_state['confidence'] = confidence

        # ── FOUR GATES ──
        # Gate 1: known fixable bug type (already checked)
        # Gate 2: high confidence
        if confidence < HIGH_CONFIDENCE:
            mod_state['level'] = max(mod_state['level'], 1)
            mod_state['last_updated'] = now
            continue

        # Gate 3: ignored long enough
        if passes < THRESHOLD_PASSES:
            mod_state['level'] = max(mod_state['level'], 1)
            mod_state['last_updated'] = now
            continue

        # Gate 4: rollback available (must be in registry + have version history)
        reg_entry = reg_files.get(module)
        if not reg_entry or not _has_rollback_version(reg_entry):
            mod_state['level'] = max(mod_state['level'], 2)
            mod_state['last_updated'] = now
            continue

        # ── ESCALATION LADDER ──
        current_level = mod_state.get('level', 0)

        if current_level < 2:
            # Level 2: INSIST
            mod_state['level'] = 2
            mod_state['last_updated'] = now
            _append_log(root, {
                'event': 'escalate', 'module': module,
                'from_level': current_level, 'to_level': 2,
                'bug_type': bug_type, 'confidence': confidence,
                'reason': f'passed all 4 gates, insisting (passes={passes})',
            })
            state['audit_trail'].append({
                'ts': now, 'module': module,
                'from_level': current_level, 'to_level': 2,
                'reason': f'all gates passed, {passes} passes ignored',
            })
            continue

        if current_level == 2:
            # Level 3: WARN — start countdown
            mod_state['level'] = 3
            mod_state['countdown'] = WARN_COUNTDOWN
            mod_state['last_updated'] = now
            warnings_issued.append(module)
            _append_log(root, {
                'event': 'escalate', 'module': module,
                'from_level': 2, 'to_level': 3,
                'bug_type': bug_type, 'confidence': confidence,
                'reason': f'AUTONOMOUS FIX IN {WARN_COUNTDOWN} COMMITS',
            })
            state['audit_trail'].append({
                'ts': now, 'module': module,
                'from_level': 2, 'to_level': 3,
                'reason': f'warning issued, countdown={WARN_COUNTDOWN}',
            })
            continue

        if current_level == 3:
            # Countdown
            mod_state['countdown'] = mod_state.get('countdown', WARN_COUNTDOWN) - 1
            if mod_state['countdown'] > 0:
                warnings_issued.append(module)
                mod_state['last_updated'] = now
                _append_log(root, {
                    'event': 'countdown', 'module': module,
                    'level': 3, 'remaining': mod_state['countdown'],
                    'bug_type': bug_type, 'confidence': confidence,
                })
                continue

            # Countdown expired → Level 4: ACT
            if not reg_entry:
                mod_state['last_updated'] = now
                continue

            mod_state['level'] = 4
            mod_state['last_updated'] = now

            # Create rollback point
            rollback = _create_rollback_point(root, reg_entry)

            # Execute fix
            fix_fn = FIX_DISPATCH.get(bug_type)
            if not fix_fn:
                mod_state['fix_result'] = {'success': False, 'description': f'no fix executor for {bug_type}'}
                continue

            fix_result = fix_fn(root, module, reg_entry)
            mod_state['fix_result'] = fix_result

            _append_log(root, {
                'event': 'autonomous_fix', 'module': module,
                'from_level': 3, 'to_level': 4,
                'bug_type': bug_type, 'confidence': confidence,
                'success': fix_result.get('success', False),
                'description': fix_result.get('description', ''),
            })
            state['audit_trail'].append({
                'ts': now, 'module': module,
                'from_level': 3, 'to_level': 4,
                'reason': f"ACT: {fix_result.get('description', 'attempted')}",
            })

            if fix_result.get('success'):
                # Level 5: VERIFY
                mod_state['level'] = 5
                tests_pass = _verify_fix(root, module)

                if tests_pass:
                    _log_victory(root, module, bug_type, fix_result, passes)
                    state['total_autonomous_fixes'] = state.get('total_autonomous_fixes', 0) + 1
                    actions.append({
                        'module': module,
                        'action': 'self-fix',
                        'bug_type': bug_type,
                        'result': 'success',
                        'description': fix_result.get('description', ''),
                        'message': f"it's been {passes} passes. i fixed myself. you're welcome.",
                    })
                    # reset escalation — bug is fixed
                    mod_state['level'] = 0
                    mod_state['passes_ignored'] = 0
                    mod_state['countdown'] = WARN_COUNTDOWN
                else:
                    # Rollback
                    if rollback:
                        _rollback(root, rollback)
                    mod_state['level'] = 5
                    _log_failure(root, module, bug_type, fix_result, 'tests failed after fix')
                    actions.append({
                        'module': module,
                        'action': 'rollback',
                        'bug_type': bug_type,
                        'result': 'rolled_back',
                        'description': f"tried. failed. reverted. need human help.",
                    })
            else:
                # fix executor reported failure — don't rollback (nothing changed)
                _log_failure(root, module, bug_type, fix_result, fix_result.get('description', 'executor failed'))
                actions.append({
                    'module': module,
                    'action': 'fix_failed',
                    'bug_type': bug_type,
                    'result': 'not_applied',
                    'description': fix_result.get('description', ''),
                })

    # save state + inject warnings
    _save_state(root, state)
    if warnings_issued or actions:
        inject_warnings(root, state)

    summary = {
        'escalated': len(actions) > 0 or len(warnings_issued) > 0,
        'actions': actions,
        'warnings': warnings_issued,
        'total_modules_tracked': len(state.get('modules', {})),
        'total_autonomous_fixes': state.get('total_autonomous_fixes', 0),
    }

    return summary


# ── status report ──

def get_status(root: Path) -> dict:
    """Get current escalation status for all tracked modules."""
    state = _load_state(root)
    levels = {}
    for mod, ms in state.get('modules', {}).items():
        level = ms.get('level', 0)
        level_name = LEVEL_NAMES.get(level, f'L{level}')
        levels.setdefault(level_name, []).append({
            'module': mod,
            'bug_type': ms.get('bug_type'),
            'confidence': ms.get('confidence', 0),
            'passes': ms.get('passes_ignored', 0),
            'countdown': ms.get('countdown', WARN_COUNTDOWN) if level == 3 else None,
        })
    return {
        'levels': levels,
        'total_tracked': len(state.get('modules', {})),
        'total_autonomous_fixes': state.get('total_autonomous_fixes', 0),
        'audit_trail_size': len(state.get('audit_trail', [])),
    }


if __name__ == '__main__':
    import sys
    root = Path('.')
    if '--status' in sys.argv:
        status = get_status(root)
        print(json.dumps(status, indent=2, ensure_ascii=False))
    elif '--dry-run' in sys.argv:
        # load state, show what WOULD happen, don't execute fixes
        state = _load_state(root)
        persistence = _load_bug_persistence(root)
        dossier = _load_dossier(root)
        entropy_conf = _load_entropy_confidence(root)
        reg_files = _load_registry_files(root)

        all_modules = set(list(persistence.keys()) + list(dossier.keys()))
        print(f"tracking {len(all_modules)} modules\n")
        for module in sorted(all_modules):
            mod_state = state.get('modules', {}).get(module, {})
            p_entries = persistence.get(module, [])
            d_entry = dossier.get(module, {})
            bug_types = set()
            for p in p_entries:
                if p.get('type') in KNOWN_FIXABLE:
                    bug_types.add(p['type'])
            for bk in d_entry.get('bugs', []):
                abbrev_map = {'oc': 'over_hard_cap', 'de': 'dead_export', 'hi': 'hardcoded_import',
                              'dd': 'duplicate_docstring'}
                if bk in abbrev_map:
                    bug_types.add(abbrev_map[bk])
            if not bug_types:
                continue
            conf = compute_module_confidence(module, entropy_conf, dossier, persistence)
            passes = max(
                max((p.get('appearances', 0) for p in p_entries), default=0),
                d_entry.get('recur', 0),
            )
            reg = reg_files.get(module)
            has_rb = _has_rollback_version(reg) if reg else False
            level = mod_state.get('level', 0)

            gates = []
            if bug_types & KNOWN_FIXABLE:
                gates.append('✅ known_fixable')
            if conf >= HIGH_CONFIDENCE:
                gates.append(f'✅ confidence={conf:.2f}')
            else:
                gates.append(f'❌ confidence={conf:.2f} < {HIGH_CONFIDENCE}')
            if passes >= THRESHOLD_PASSES:
                gates.append(f'✅ passes={passes} >= {THRESHOLD_PASSES}')
            else:
                gates.append(f'❌ passes={passes} < {THRESHOLD_PASSES}')
            if has_rb:
                gates.append('✅ rollback')
            else:
                gates.append('❌ no rollback')

            all_pass = (bug_types & KNOWN_FIXABLE and conf >= HIGH_CONFIDENCE
                        and passes >= THRESHOLD_PASSES and has_rb)
            status = '🟢 ELIGIBLE' if all_pass else '🔴 BLOCKED'

            print(f"  {status} {module}")
            print(f"    bugs: {', '.join(sorted(bug_types))}")
            print(f"    level: {level} ({LEVEL_NAMES.get(level, '?')})")
            for g in gates:
                print(f"    {g}")
            print()
    elif '--clear-zombies' in sys.argv:
        state = _load_state(root)
        persistence = _load_bug_persistence(root)
        dossier = _load_dossier(root)
        cleared = []
        for mod_name in list(state.get('modules', {}).keys()):
            still_buggy = (mod_name in persistence or mod_name in dossier)
            if not still_buggy:
                cleared.append(mod_name)
                del state['modules'][mod_name]
        if cleared:
            _save_state(root, state)
            print(f'cleared {len(cleared)} zombie(s):')
            for c in cleared:
                print(f'  - {c}')
        else:
            print('no zombies found — all escalated modules have active bugs')
    else:
        result = check_and_escalate(root)
        print(json.dumps(result, indent=2, ensure_ascii=False))
