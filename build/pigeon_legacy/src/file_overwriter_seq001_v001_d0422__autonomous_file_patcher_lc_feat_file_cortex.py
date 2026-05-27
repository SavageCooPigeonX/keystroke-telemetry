"""file_overwriter_seq001_v001 — autonomous file patcher triggered by sim grades.

When run_sim grades a file as needs_change=True (conf >= threshold), this module:
  1. Reads the full file source
  2. Calls DeepSeek chat to generate a minimal, valid replacement
  3. Backs up original to logs/file_overwrite_backups/<stem>/<ts>.py.bak
  4. Applies overwrite atomically (write tmp → rename)
  5. Logs to logs/file_overwrites.jsonl
  6. Updates file_profiles.json cortex with self_fix_attempted event

Manual:
  py -c "
  from pathlib import Path; import importlib.util
  spec = importlib.util.spec_from_file_location('fo', sorted(Path('src').glob('file_overwriter*.py'))[-1])
  m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
  r = m.overwrite_file('tc_gemini', 'fix rate limit retry logic', dry_run=True)
  print(r['diff'][:400])
  "
"""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | ~220 lines | ~2,400 tokens
# DESC:   autonomous_file_patcher
# INTENT: feat_file_cortex
# LAST:   2026-04-22
# SESSIONS: 1
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   2026-04-22T01:30:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  fix atomic write Windows WinError 183
# EDIT_AUTHOR: copilot
# EDIT_STATE: active
# ── /pulse ──

from __future__ import annotations
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request as _ur
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
OVERWRITE_LOG = ROOT / 'logs' / 'file_overwrites.jsonl'
BACKUP_DIR = ROOT / 'logs' / 'file_overwrite_backups'

# Only auto-overwrite at this confidence — below this it stays dry_run
AUTO_OVERWRITE_THRESHOLD = 0.85

_DEEPSEEK_URL = 'https://api.deepseek.com/v1/chat/completions'
_DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_CODING_MODEL') or os.environ.get('DEEPSEEK_MODEL') or 'deepseek-v4-pro'

_PATCH_SYSTEM = """You are an expert Python programmer performing surgical code patches.
You will be given a Python source file and a targeted intent.

Output ONLY a series of search-replace blocks in this exact format — nothing else:

<<<SEARCH
<exact lines from the original file to replace>
===
<new lines to substitute>
>>>REPLACE

Rules:
- Include 2-3 lines of surrounding context in each SEARCH block so matches are unambiguous.
- SEARCH text must match the original file character-for-character (spaces, indentation).
- Make MINIMAL changes — only touch what the intent requires.
- If nothing needs changing, output exactly: NO_CHANGES
- Do NOT output the full file. Do NOT explain. Only output the blocks."""

_FULL_OVERWRITE_SYSTEM = """You are the autonomous coding agent for a single Python file in the Pigeon system.
You will be given complete context for ONE file and ONE task. You own this file completely.
Your job: emit the full, correct, new version of this file. Nothing else.

OUTPUT FORMAT: emit only the complete Python file — no markdown fences, no explanation.
If the file does not need any change, emit exactly: NO_CHANGES

PIGEON HARD RULES (these are non-negotiable — violations cause CI failure):
1. Max 200 lines / ~2000 tokens. If your output would exceed this, emit: SPLIT_NEEDED
2. No hardcoded imports — use the dynamic loader pattern: _load_glob_module(root, 'src', 'stem_prefix*')
3. The pulse header must be the first block — update EDIT_TS to now (UTC ISO), increment VER, set EDIT_WHY to a one-line summary of what you changed.
4. Do NOT rename or remove any symbol listed in IMPORTERS — those callers will break.
5. Do NOT duplicate logic that belongs to SIBLINGS — each file owns exactly one concern.
6. If you add a new dependency, use _load_glob_module — never import by hardcoded name.

You are written blind — the template below is your complete context. Do not assume anything not stated."""

_POST_PATCH_GRADE_SYSTEM = """You are a code execution grader. A surgical patch was applied to a Python file.
Grade the assembled change independently — you are acting on behalf of this file alone.

Given: the intent, the applied diff, and the patched code preview.

Return JSON only:
{"code_grade": 0.0-1.0, "correct": true/false, "issues": "one line or empty", "verdict": "accept|flag|reject"}

Rules:
- code_grade > 0.7 = good change, 0.4-0.7 = marginal, < 0.4 = suspect
- correct = true only if the diff clearly and directly addresses the stated intent
- issues = any visible logic error, missing import, broken call, or unintended side effect
- verdict: accept = patch stands | flag = patch applied but operator should review | reject = rollback recommended
- Be strict. A bad patch that compiles is worse than no patch."""


def _load_deepseek_key(root: Path) -> str | None:
    v = os.environ.get('DEEPSEEK_API_KEY', '')
    if v:
        return v
    env = root / '.env'
    if env.exists():
        for line in env.read_text('utf-8', errors='ignore').splitlines():
            if line.startswith('DEEPSEEK_API_KEY='):
                v = line.split('=', 1)[1].strip()
                if v:
                    return v
    return None


def _call_deepseek(system: str, user: str, api_key: str, timeout: int = 60) -> str:
    """Call DeepSeek chat API. Returns raw response text."""
    body = json.dumps({
        'model': _DEEPSEEK_MODEL,
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user},
        ],
        'max_tokens': 4096,
        'temperature': 0.1,
    }).encode('utf-8')
    req = _ur.Request(
        _DEEPSEEK_URL, data=body,
        headers={'Content-Type': 'application/json',
                 'Authorization': f'Bearer {api_key}'},
        method='POST',
    )
    with _ur.urlopen(req, timeout=timeout) as resp:
        d = json.loads(resp.read())
    return d['choices'][0]['message']['content'].strip()


def _parse_search_replace_blocks(text: str) -> list[tuple[str, str]]:
    """Parse <<<SEARCH ... === ... >>>REPLACE blocks from DeepSeek response.
    Returns list of (search_text, replace_text) pairs.
    """
    blocks: list[tuple[str, str]] = []
    pattern = re.compile(
        r'<<<SEARCH\s*\n(.*?)\n===\s*\n(.*?)\n>>>REPLACE',
        re.DOTALL,
    )
    for m in pattern.finditer(text):
        blocks.append((m.group(1), m.group(2)))
    return blocks


def _apply_search_replace(original: str, blocks: list[tuple[str, str]]) -> tuple[str, list[str]]:
    """Apply search-replace blocks to source text.
    Returns (patched_source, list_of_errors).
    """
    result = original
    errors: list[str] = []
    for i, (search, replace) in enumerate(blocks):
        if search in result:
            result = result.replace(search, replace, 1)
        else:
            # try stripping trailing whitespace differences
            stripped_search = '\n'.join(l.rstrip() for l in search.splitlines())
            stripped_result = '\n'.join(l.rstrip() for l in result.splitlines())
            if stripped_search in stripped_result:
                # rebuild with stripped comparison — apply via line scan
                result_lines = result.splitlines(keepends=True)
                search_lines = search.splitlines()
                n = len(search_lines)
                applied = False
                for j in range(len(result_lines) - n + 1):
                    window = [l.rstrip() for l in result_lines[j:j + n]]
                    if window == search_lines:
                        indent = result_lines[j][: len(result_lines[j]) - len(result_lines[j].lstrip())]
                        result = (
                            ''.join(result_lines[:j])
                            + replace
                            + ('\n' if not replace.endswith('\n') else '')
                            + ''.join(result_lines[j + n:])
                        )
                        applied = True
                        break
                if not applied:
                    errors.append(f'block {i + 1}: SEARCH text not found')
            else:
                errors.append(f'block {i + 1}: SEARCH text not found (tried strip)')
    return result, errors


def _find_file(stem: str, root: Path) -> Path | None:
    """Find the Python file for a given stem. Returns first match."""
    for pattern in (
        f'src/{stem}.py', f'src/{stem}_seq*.py', f'src/**/{stem}.py', f'src/**/{stem}_seq*.py',
        f'client/{stem}.py', f'pigeon_compiler/**/{stem}.py', f'pigeon_brain/**/{stem}.py',
        f'{stem}.py',
    ):
        hits = list(root.glob(pattern))
        if hits:
            return hits[0]
    return None


def _find_target_file(stem: str, root: Path, target_path: str | None = None) -> Path | None:
    """Find an approved target path first, then fall back to stem lookup."""
    rel = str(target_path or '').strip().replace('\\', '/')
    if rel and not rel.startswith('/') and '..' not in Path(rel).parts:
        candidate = (root / rel).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            candidate = None
        if candidate and candidate.exists() and candidate.is_file() and candidate.suffix == '.py':
            return candidate
    return _find_file(stem, root)


def _make_diff(original: str, patched: str) -> str:
    """Simple line-level diff for display (not git diff)."""
    orig_lines = original.splitlines()
    new_lines = patched.splitlines()
    added = sum(1 for l in new_lines if l not in orig_lines)
    removed = sum(1 for l in orig_lines if l not in new_lines)
    changed = min(added, removed)
    net = len(new_lines) - len(orig_lines)
    return (f'+{added} lines added, -{removed} lines removed, '
            f'~{changed} changed, net {net:+d}')


def _backup_file(path: Path, root: Path) -> Path:
    """Copy file to logs/file_overwrite_backups/<stem>/<ts>.py.bak."""
    ts = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    bak_dir = root / 'logs' / 'file_overwrite_backups' / path.stem
    bak_dir.mkdir(parents=True, exist_ok=True)
    bak_path = bak_dir / f'{ts}.py.bak'
    shutil.copy2(path, bak_path)
    return bak_path


def _atomic_write(path: Path, content: str) -> None:
    """Write content to a tmp file in the same dir, then rename (atomic on same FS)."""
    tmp = path.with_suffix('.tmp_overwrite')
    tmp.write_text(content, encoding='utf-8')
    os.replace(tmp, path)  # os.replace works on Windows even if dest exists


def _run_regression(stem: str, path: Path, bak_path: Path, root: Path) -> dict:
    """Run post-patch regression: py_compile syntax check, then matching test file.
    Restores backup if either step fails.
    Returns {passed, failed, error, test_file}.
    """
    out = {'passed': False, 'failed': False, 'error': '', 'test_file': ''}

    # 1. Syntax check
    r = subprocess.run(
        [sys.executable, '-m', 'py_compile', str(path)],
        capture_output=True, text=True, timeout=10,
    )
    if r.returncode != 0:
        shutil.copy2(bak_path, path)
        out['failed'] = True
        out['error'] = f'syntax: {(r.stderr or r.stdout)[:200]}'
        print(f'  [regression] ✗ syntax failed for {stem} — restored')
        return out

    # 2. Find matching test file in tests/interlink/
    test_dir = root / 'tests' / 'interlink'
    stem_short = stem.split('_seq')[0]  # e.g. tc_gemini
    test_file: Path | None = None
    for pattern in (
        f'test_{stem}.py',
        f'test_{stem_short}.py',
        f'test_{stem_short}_seq*.py',
    ):
        hits = sorted(test_dir.glob(pattern))
        if hits:
            test_file = hits[-1]  # newest version
            break

    if test_file is None:
        # No test file — syntax passed, that's the full check
        out['passed'] = True
        out['test_file'] = 'none (no matching test)'
        print(f'  [regression] ✓ syntax OK, no test file for {stem}')
        return out

    out['test_file'] = test_file.name
    r = subprocess.run(
        [sys.executable, str(test_file)],
        capture_output=True, text=True, timeout=30, cwd=str(root),
    )
    if r.returncode != 0:
        shutil.copy2(bak_path, path)
        out['failed'] = True
        snippet = (r.stdout + r.stderr)[:300]
        out['error'] = f'test {test_file.name}: {snippet}'
        print(f'  [regression] ✗ test failed for {stem} — restored')
        return out

    out['passed'] = True
    print(f'  [regression] ✓ {test_file.name} passed for {stem}')
    return out


def _run_post_patch_grader(
        stem: str, intent_text: str, diff: str,
        patched_preview: str, api_key: str, root: Path,
) -> dict:
    """Grade the assembled code after DeepSeek applies the patch.

    This fires AFTER the patch is written and regression passes — it grades
    whether the code change actually fulfills the intent correctly.
    Files are graded independently: each file gets its own code quality verdict.

    Returns: {code_grade, correct, issues, verdict, stem}
    """
    result = {'code_grade': 0.5, 'correct': False, 'issues': '', 'verdict': 'flag', 'stem': stem}
    if not api_key or not diff:
        return result
    user_prompt = (
        f'INTENT: {intent_text[:300]}\n\n'
        f'FILE: {stem}\n\n'
        f'APPLIED DIFF:\n{diff[:800]}\n\n'
        f'PATCHED CODE PREVIEW:\n{patched_preview[:600]}\n\n'
        f'Grade this patch independently for this file.'
    )
    try:
        raw = _call_deepseek(_POST_PATCH_GRADE_SYSTEM, user_prompt, api_key, timeout=30)
        start = raw.find('{')
        end = raw.rfind('}') + 1
        parsed = json.loads(raw[start:end]) if start >= 0 else {}
        result['code_grade'] = float(parsed.get('code_grade', 0.5))
        result['correct'] = bool(parsed.get('correct', False))
        result['issues'] = str(parsed.get('issues', ''))[:200]
        result['verdict'] = str(parsed.get('verdict', 'flag'))
        print(f'  [post-grade] {stem}: grade={result["code_grade"]:.2f} verdict={result["verdict"]}')
        # Log to grader results for observatory / intent_bp
        _log_post_patch_grade(stem, intent_text, diff, result, root)
    except Exception as e:
        print(f'  [post-grade] {stem} failed: {e}')
    return result


def _log_post_patch_grade(stem: str, intent_text: str, diff: str, grade: dict, root: Path) -> None:
    """Append post-patch grade to logs/post_patch_grades.jsonl."""
    log = root / 'logs' / 'post_patch_grades.jsonl'
    log.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'stem': stem,
        'intent_preview': intent_text[:80],
        'diff_preview': diff[:200],
        'code_grade': grade['code_grade'],
        'correct': grade['correct'],
        'issues': grade['issues'],
        'verdict': grade['verdict'],
    }
    try:
        with open(log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except Exception:
        pass


def _update_cortex(stem: str, root: Path, fix: str, success: bool, trigger: str) -> None:
    """Fire update_file_cortex without hard-importing file_sim (avoids circular)."""
    try:
        import importlib.util
        matches = sorted((root / 'src').glob('file_sim*.py'), key=lambda p: len(p.name))
        if not matches:
            return
        spec = importlib.util.spec_from_file_location('file_sim', matches[-1])
        m = importlib.util.module_from_spec(spec)
        if spec and spec.loader:
            spec.loader.exec_module(m)
            m.update_file_cortex(stem, root, event={
                'type': 'self_fix_attempted',
                'fix': fix,
                'success': success,
                'trigger': trigger,
            })
    except Exception:
        pass


def _build_overwrite_context(stem: str, intent_text: str, root: Path,
                             grade_result: dict | None = None) -> str:
    """Build the full blind-write context template for DeepSeek.

    Assembles everything DeepSeek needs to rewrite the file correctly
    without reading any other file: contract, constraints, toolkit, task.
    If a file cannot be written blind from this template, it is too coupled.
    """
    import ast as _ast

    path = _find_file(stem, root)
    if path is None:
        return f'INTENT: {intent_text}\n\nERROR: file not found for stem {stem}'

    source = path.read_text('utf-8', errors='replace')
    lines = source.splitlines()

    # ── Pulse header (first block — the file's identity card) ──────────────
    pulse_lines = [l for l in lines[:25] if l.startswith('#')]
    pulse_header = '\n'.join(pulse_lines) if pulse_lines else lines[:20] and '\n'.join(lines[:20])

    # ── Registry entry: tokens, bugs, version ──────────────────────────────
    reg_entry: dict = {}
    try:
        reg_path = root / 'pigeon_registry.json'
        if reg_path.exists():
            registry = json.loads(reg_path.read_text('utf-8', errors='ignore'))
            for _path, _entry in registry.items():
                if stem in Path(_path).stem:
                    reg_entry = _entry
                    break
    except Exception:
        pass

    token_count = reg_entry.get('tokens', len(source) // 4)
    bug_codes = reg_entry.get('bug_keys', [])
    version = reg_entry.get('ver', '?')

    # ── Importers: who calls this file (these exports must not be renamed) ──
    importers: list[str] = []
    exported_names: list[str] = []
    try:
        # find exported names via AST (top-level defs/classes not prefixed with _)
        tree = _ast.parse(source)
        exported_names = [
            n.name for n in _ast.walk(tree)
            if isinstance(n, (_ast.FunctionDef, _ast.AsyncFunctionDef, _ast.ClassDef))
            and not n.name.startswith('_')
        ]
        # find who imports this stem from the registry
        reg_path2 = root / 'pigeon_registry.json'
        if reg_path2.exists():
            registry2 = json.loads(reg_path2.read_text('utf-8', errors='ignore'))
            for _path2, _entry2 in registry2.items():
                if stem in str(_entry2.get('imports', [])):
                    importers.append(Path(_path2).stem)
        # fallback: grep src/ for imports of the stem
        if not importers:
            for py in (root / 'src').glob('*.py'):
                if py.stem == stem:
                    continue
                try:
                    txt = py.read_text('utf-8', errors='ignore')
                    if stem in txt:
                        importers.append(py.stem)
                except Exception:
                    pass
    except Exception:
        pass

    # ── Dependencies: what this file loads ─────────────────────────────────
    deps: list[str] = []
    try:
        tree2 = _ast.parse(source)
        for node in _ast.walk(tree2):
            if isinstance(node, _ast.Import):
                for alias in node.names:
                    deps.append(alias.name.split('.')[0])
            elif isinstance(node, _ast.ImportFrom):
                if node.module:
                    deps.append(node.module.split('.')[0])
        deps = sorted(set(deps) - {'__future__', 'json', 'os', 're', 'sys',
                                    'time', 'pathlib', 'datetime', 'threading',
                                    'subprocess', 'shutil', 'tempfile'})[:12]
    except Exception:
        pass

    # ── Split lineage ───────────────────────────────────────────────────────
    lineage_section = ''
    try:
        split_log = root / 'logs' / 'split_events.jsonl'
        if split_log.exists():
            lin_map: dict = {}
            for _ln in split_log.read_text('utf-8', errors='ignore').strip().splitlines():
                try:
                    _ev = json.loads(_ln)
                    for _ch in _ev.get('child_stems', []):
                        lin_map[_ch] = {
                            'parent': _ev.get('parent_stem', ''),
                            'siblings': [s for s in _ev.get('child_stems', []) if s != _ch],
                        }
                except Exception:
                    pass
            if stem in lin_map:
                _l = lin_map[stem]
                lineage_section = (
                    f"\nSPLIT LINEAGE\n"
                    f"  born from:  {_l['parent']}\n"
                    f"  siblings:   {', '.join(_l['siblings'][:4]) or 'none'}\n"
                    f"  rule:       do NOT duplicate logic owned by siblings"
                )
    except Exception:
        pass

    # ── MANIFEST chain: last 3 entries nearest this file ───────────────────
    manifest_section = ''
    try:
        manifest = root / 'MANIFEST.md'
        if manifest.exists():
            mlines = manifest.read_text('utf-8', errors='ignore').splitlines()
            relevant = [l for l in mlines if stem in l or path.parent.name in l][:3]
            if relevant:
                manifest_section = '\nMANIFEST CHAIN (last relevant entries):\n' + '\n'.join(f'  {l}' for l in relevant)
    except Exception:
        pass

    # ── Rework history: last 2 edit_why for this stem ──────────────────────
    rework_section = ''
    try:
        rw_path = root / 'rework_log.json'
        if rw_path.exists():
            rw = json.loads(rw_path.read_text('utf-8', errors='ignore'))
            # rework_log can be list or dict
            entries = rw if isinstance(rw, list) else rw.get(stem, [])
            if isinstance(rw, dict):
                entries = []
                for k, v in rw.items():
                    if stem in k:
                        entries = v if isinstance(v, list) else [v]
                        break
            recent = entries[-2:] if entries else []
            if recent:
                rework_section = '\nREWORK HISTORY:\n' + '\n'.join(
                    f"  {e.get('edit_why', str(e))}" for e in recent
                )
    except Exception:
        pass

    # ── Sim winner: what the sim said to do ────────────────────────────────
    sim_section = ''
    try:
        sim_log = root / 'logs' / 'tc_sim_results.jsonl'
        if sim_log.exists():
            sim_lines = sim_log.read_text('utf-8', errors='ignore').strip().splitlines()
            # find latest entry where this stem appears in top_files or action
            for _sl in reversed(sim_lines[-50:]):
                try:
                    _se = json.loads(_sl)
                    if stem in str(_se.get('top_files', '')) or stem in str(_se.get('action', '')):
                        sim_section = (
                            f"\nSIM WINNER: {_se.get('sim_name','?')} (conf={_se.get('confidence',0):.2f})\n"
                            f"  action: {str(_se.get('action', ''))[:200]}"
                        )
                        break
                except Exception:
                    pass
    except Exception:
        pass

    # ── Grade context ───────────────────────────────────────────────────────
    grade_section = ''
    if grade_result:
        grade_section = (
            f"\nGRADE: {grade_result.get('confidence', 0):.2f} | "
            f"REASON: {grade_result.get('reason', '')[:120]}"
        )

    # ── Assemble the template ───────────────────────────────────────────────
    importer_lines = '\n'.join(
        f'  {imp}: uses [{", ".join(exported_names[:8])}]' for imp in importers[:6]
    ) or '  (none found — you may safely refactor internal names)'

    return f"""═══════════════════════════════════════════════════════
TASK: {intent_text[:400]}
{grade_section}
═══════════════════════════════════════════════════════

TARGET FILE
  path:        {path.relative_to(root)}
  stem:        {stem}
  version:     v{version} → write v{int(version)+1 if str(version).isdigit() else version}+1
  tokens:      {token_count} / 2000 cap
  bug codes:   {', '.join(bug_codes) if bug_codes else 'none'}

PULSE HEADER (maintain this format — update EDIT_TS, EDIT_WHY, VER)
{pulse_header}

IMPORTERS (these symbols must not be renamed or removed)
{importer_lines}

DEPENDENCIES (available via dynamic loader)
  {', '.join(deps) if deps else 'standard library only'}
{lineage_section}
{manifest_section}
{rework_section}
{sim_section}

FULL SOURCE (write a complete new version below — nothing else)
```python
{source}
```"""


def overwrite_file(
        stem: str,
        intent_text: str,
        grade_result: dict | None = None,
        root: Path | None = None,
        dry_run: bool = True,
        approved: bool = False,
        target_path: str | None = None,
        _patch_override: str | None = None,
) -> dict:
    """Patch a file to fulfil an intent.

    Args:
        stem:          module stem (e.g. 'tc_gemini', 'w_gpmo')
        intent_text:   the operator intent driving the change
        grade_result:  dict from grade_file_for_intent (optional — used for context)
        root:          workspace root (default ROOT)
        dry_run:       if True, generates patch but does NOT write to disk

    Returns:
        {applied, diff, error, backup_path, patched_preview, dry_run}
    """
    root = root or ROOT
    out: dict = {'applied': False, 'diff': '', 'error': '',
                 'backup_path': '', 'patched_preview': '', 'dry_run': dry_run,
                 'regression': {}}

    api_key = _load_deepseek_key(root)
    if not api_key and not _patch_override:
        out['error'] = 'no DEEPSEEK_API_KEY in .env'
        return out

    path = _find_target_file(stem, root, target_path)
    if path is None:
        out['error'] = f'{stem} — file not found'
        return out

    original = path.read_text('utf-8', errors='replace')
    confidence = (grade_result or {}).get('confidence', 0.0)
    is_approved = approved or bool((grade_result or {}).get('approved'))
    if not dry_run and not is_approved:
        out['error'] = 'live overwrite blocked: missing file approval'
        _log_overwrite(stem, intent_text, dry_run=False, success=False,
                       error=out['error'], diff='', backup_path='',
                       regression={}, root=root)
        return out

    user_prompt = _build_overwrite_context(stem, intent_text, root, grade_result)
    raw = _patch_override

    print(f'  [overwriter] calling DeepSeek for {stem} (conf={confidence:.2f})…')
    t0 = time.perf_counter()
    try:
        if raw is None:
            raw = _call_deepseek(_FULL_OVERWRITE_SYSTEM, user_prompt, api_key)
    except Exception as e:
        out['error'] = f'DeepSeek call failed: {e}'
        _log_overwrite(stem, intent_text, dry_run=dry_run, success=False,
                       error=out['error'], diff='', backup_path='', root=root)
        return out
    elapsed = time.perf_counter() - t0
    print(f'  [overwriter] DeepSeek responded in {elapsed:.1f}s')

    # Handle sentinel responses
    first_line = raw.strip().splitlines()[0].upper() if raw.strip() else ''
    if first_line.startswith('NO_CHANGES'):
        out['diff'] = 'no changes needed'
        print(f'  [overwriter] {stem}: DeepSeek says no changes needed')
        return out
    if first_line.startswith('SPLIT_NEEDED'):
        out['error'] = f'{stem}: DeepSeek flagged SPLIT_NEEDED — file is overcap, pigeon should split'
        print(f'  [overwriter] ✗ {stem}: SPLIT_NEEDED — skipping write')
        return out

    blocks = _parse_search_replace_blocks(raw)
    if blocks:
        patched, errors = _apply_search_replace(original, blocks)
        if errors:
            out['error'] = '; '.join(errors[:3])
            _log_overwrite(stem, intent_text, dry_run=dry_run, success=False,
                           error=out['error'], diff='', backup_path='',
                           regression={}, root=root)
            return out
    else:
        # Strip markdown fences if DeepSeek wrapped the output
        patched = raw.strip()
    if patched.startswith('```'):
        patched = re.sub(r'^```[a-zA-Z]*\n?', '', patched)
        patched = re.sub(r'\n?```$', '', patched)
        patched = patched.strip()

    if not patched:
        out['error'] = f'empty response from DeepSeek'
        return out

    if patched == original.strip():
        out['diff'] = 'no changes (identical output)'
        return out

    diff = _make_diff(original, patched)
    out['diff'] = diff
    out['patched_preview'] = patched[:600]

    if dry_run:
        print(f'  [overwriter] DRY RUN — would apply: {diff}')
        out['dry_run'] = True
        _log_overwrite(stem, intent_text, dry_run=True, success=False,
                       error='', diff=diff, backup_path='', regression={}, root=root)
        return out

    # Live write — backup first
    bak_path = _backup_file(path, root)
    out['backup_path'] = str(bak_path)
    try:
        _atomic_write(path, patched)
    except Exception as e:
        shutil.copy2(bak_path, path)
        out['error'] = f'write failed (restored): {e}'
        _log_overwrite(stem, intent_text, dry_run=False, success=False,
                       error=out['error'], diff=diff,
                       backup_path=str(bak_path), regression={}, root=root)
        return out

    # Regression TDD — syntax check + matching test file
    reg = _run_regression(stem, path, bak_path, root)
    out['regression'] = reg
    if reg['failed']:
        # backup already restored by _run_regression
        out['applied'] = False
        out['error'] = f'regression failed — restored: {reg["error"][:120]}'
        print(f'  [overwriter] ✗ {stem}: regression rolled back patch')
    else:
        out['applied'] = True
        print(f'  [overwriter] ✓ applied {path.name} | {diff} | test: {reg["test_file"]}')
        # ── Post-patch code grader ────────────────────────────────────────────
        # Grader fires AFTER DeepSeek assembles + regression passes.
        # Each file is graded independently on its own code quality.
        # This is the execution-quality gate — not the pre-sim intent gate.
        post_grade = _run_post_patch_grader(
            stem, intent_text, diff, patched, api_key, root)
        out['post_patch_grade'] = post_grade
        if post_grade.get('verdict') == 'reject':
            # Grader recommends rollback — restore from backup
            shutil.copy2(bak_path, path)
            out['applied'] = False
            out['error'] = (f'post-patch grader rejected: {post_grade.get("issues","")[:120]}')
            print(f'  [overwriter] ✗ {stem}: post-grade REJECT → restored')

    _log_overwrite(stem, intent_text, dry_run=False, success=out['applied'],
                   error=out['error'], diff=diff,
                   backup_path=str(bak_path), regression=reg,
                   post_grade=out.get('post_patch_grade', {}), root=root)
    _update_cortex(stem, root,
                   fix='file_overwriter',
                   success=out['applied'],
                   trigger=f'sim_grade conf={confidence:.2f}')
    return out


def _log_overwrite(stem: str, intent: str, dry_run: bool, success: bool,
                   error: str, diff: str, backup_path: str,
                   regression: dict, root: Path,
                   post_grade: dict | None = None) -> None:
    overwrite_log = root / 'logs' / 'file_overwrites.jsonl'
    overwrite_log.parent.mkdir(parents=True, exist_ok=True)
    pg = post_grade or {}
    entry = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'stem': stem,
        'intent_preview': intent[:80],
        'dry_run': dry_run,
        'applied': success,
        'diff': diff,
        'backup_path': backup_path,
        'error': error,
        'regression_passed': regression.get('passed', None),
        'regression_test': regression.get('test_file', ''),
        'regression_error': regression.get('error', ''),
        # Post-patch code grade (grader fires after DeepSeek assembles, not before)
        'post_grade': pg.get('code_grade'),
        'post_grade_verdict': pg.get('verdict', ''),
        'post_grade_correct': pg.get('correct'),
        'post_grade_issues': pg.get('issues', ''),
    }
    with open(overwrite_log, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def pending_overwrites(root: Path | None = None) -> list[dict]:
    """Return sim grades that are awaiting overwrite (needs_change=True, not yet overwritten)."""
    root = root or ROOT
    sim_log = root / 'logs' / 'sim_results.jsonl'
    if not sim_log.exists():
        return []

    # Build set of already-overwritten stems from overwrite log
    done: set[str] = set()
    if OVERWRITE_LOG.exists():
        for line in OVERWRITE_LOG.read_text('utf-8', errors='ignore').splitlines():
            try:
                e = json.loads(line)
                if e.get('applied'):
                    done.add(e['stem'])
            except Exception:
                pass

    pending = []
    for line in sim_log.read_text('utf-8', errors='ignore').splitlines():
        try:
            e = json.loads(line)
            if (e.get('needs_change') and not e.get('self_excluded')
                    and e.get('confidence', 0) >= AUTO_OVERWRITE_THRESHOLD
                    and e.get('file_stem') not in done):
                pending.append(e)
        except Exception:
            pass
    return pending
