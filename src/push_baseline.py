"""Push Baseline — drift measurement + semantic void detection on every push.

Every push triggers a baseline assessment of changed modules.
Modules detect their own semantic voids (missing context) and
request context growth into their profiles. If unsure → spike
entropy + file a context request. This is the truth gate.

State machine integration:
  push → assess changed modules → compare to genesis snapshot →
  detect drift → find semantic voids → spike entropy if unsure →
  grow module context → inject drift report into prompt layer

Launch: called automatically by push_cycle.run_push_cycle()
Manual: py -m src.push_baseline
"""

from __future__ import annotations

import ast
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── telemetry:pulse ──
# EDIT_TS:   2026-04-12T18:30:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  create push baseline drift gate
# EDIT_AUTHOR: copilot
# EDIT_STATE: harvested
# ── /pulse ──

BASELINE_DB = 'logs/push_baseline_state.json'
CONTEXT_REQUESTS = 'logs/context_requests.jsonl'
DRIFT_LOG = 'logs/baseline_drift.jsonl'
ENTROPY_MAP = 'logs/entropy_map.json'

# ── baseline questions (fixed at genesis, never change) ──────
BASELINE_QUESTIONS = {
    'import_count': 'how many imports does this module have?',
    'export_count': 'how many public functions/classes does it export?',
    'line_count': 'how many non-empty lines?',
    'token_ratio': 'what is the code-to-comment token ratio?',
    'coupling_score': 'how many other modules import this one?',
    'semantic_hash': 'what is the structural hash of its public API?',
}

# ── drift thresholds ──────────────────────────────────────────
DRIFT_THRESHOLDS = {
    'import_count': 0.4,     # 40% change = drift
    'export_count': 0.3,     # 30% change = drift
    'line_count': 0.5,       # 50% change = drift
    'token_ratio': 0.3,      # 30% ratio change = drift
    'coupling_score': 0.5,   # 50% coupling change = drift
    'semantic_hash': 1.0,    # any hash change = drift (binary)
}

ENTROPY_SPIKE = 0.15  # how much to spike entropy on void detection


def _load_db(root: Path) -> dict[str, Any]:
    path = root / BASELINE_DB
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    return {}


def _save_db(root: Path, db: dict[str, Any]) -> None:
    path = root / BASELINE_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(db, indent=2, ensure_ascii=False), encoding='utf-8')


def _count_lines(filepath: Path) -> int:
    try:
        return sum(1 for ln in filepath.read_text(encoding='utf-8').splitlines() if ln.strip())
    except Exception:
        return 0


def _get_imports(filepath: Path) -> list[str]:
    try:
        tree = ast.parse(filepath.read_text(encoding='utf-8'))
    except Exception:
        return []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def _get_public_api(filepath: Path) -> list[str]:
    try:
        tree = ast.parse(filepath.read_text(encoding='utf-8'))
    except Exception:
        return []
    return [
        node.name for node in ast.iter_child_nodes(tree)
        if isinstance(node, (ast.FunctionDef, ast.ClassDef))
        and not node.name.startswith('_')
    ]


def _semantic_hash(filepath: Path) -> str:
    """Hash the public API surface — names + arg counts. Detects structural drift."""
    try:
        tree = ast.parse(filepath.read_text(encoding='utf-8'))
    except Exception:
        return 'parse_error'
    sigs = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
            n_args = len(node.args.args)
            sigs.append(f'{node.name}/{n_args}')
        elif isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
            methods = [n.name for n in ast.walk(node) if isinstance(n, ast.FunctionDef)]
            sigs.append(f'{node.name}:[{",".join(sorted(methods))}]')
    raw = '|'.join(sorted(sigs))
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _token_ratio(filepath: Path) -> float:
    """Ratio of code tokens to comment tokens. Low = heavily commented."""
    try:
        source = filepath.read_text(encoding='utf-8')
    except Exception:
        return 0.0
    code_tokens = 0
    comment_tokens = 0
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith('#'):
            comment_tokens += len(stripped.split())
        elif stripped:
            code_tokens += len(stripped.split())
    total = code_tokens + comment_tokens
    return round(code_tokens / max(total, 1), 3)


def _count_importers(filepath: Path, root: Path) -> int:
    """Count how many other .py files import this module."""
    stem = filepath.stem
    count = 0
    for py in root.rglob('*.py'):
        if py == filepath or '__pycache__' in str(py):
            continue
        try:
            text = py.read_text(encoding='utf-8', errors='ignore')
            if f'import {stem}' in text or f'from {stem}' in text:
                count += 1
        except Exception:
            continue
    return count


def measure_module(filepath: Path, root: Path) -> dict[str, Any]:
    """Take a full baseline measurement of a module."""
    imports = _get_imports(filepath)
    exports = _get_public_api(filepath)
    return {
        'import_count': len(imports),
        'export_count': len(exports),
        'line_count': _count_lines(filepath),
        'token_ratio': _token_ratio(filepath),
        'coupling_score': _count_importers(filepath, root),
        'semantic_hash': _semantic_hash(filepath),
        'imports': imports,
        'exports': exports,
    }


def _compute_drift(genesis: dict, current: dict) -> dict[str, Any]:
    """Compare current measurement to genesis snapshot. Returns per-question drift."""
    drift = {}
    for q_key, threshold in DRIFT_THRESHOLDS.items():
        gen_val = genesis.get(q_key, 0)
        cur_val = current.get(q_key, 0)

        if q_key == 'semantic_hash':
            # binary: changed or not
            drifted = gen_val != cur_val
            magnitude = 1.0 if drifted else 0.0
        else:
            # numeric: relative change
            base = max(abs(gen_val) if isinstance(gen_val, (int, float)) else 1, 1)
            if isinstance(cur_val, (int, float)) and isinstance(gen_val, (int, float)):
                magnitude = abs(cur_val - gen_val) / base
            else:
                magnitude = 0.0
            drifted = magnitude > threshold

        drift[q_key] = {
            'genesis': gen_val,
            'current': cur_val,
            'magnitude': round(magnitude, 3),
            'threshold': threshold,
            'drifted': drifted,
        }
    return drift


def detect_semantic_voids(filepath: Path, root: Path, current: dict) -> list[dict]:
    """Detect what a module DOESN'T know about itself — the missing context.

    A semantic void is a gap in self-understanding:
    - Functions with no docstring (purpose unknown)
    - Imports it can't explain (why does it need this?)
    - Exports nobody calls (dead tissue or future API?)
    - Try/except that swallows errors (hiding failures)
    - Magic numbers or hardcoded paths (unexplained decisions)
    - Functions over 30 lines (complexity it hasn't decomposed)
    """
    voids = []
    try:
        source = filepath.read_text(encoding='utf-8')
        tree = ast.parse(source)
    except Exception:
        voids.append({
            'type': 'parse_failure',
            'severity': 'critical',
            'question': 'this file cannot be parsed — syntax error prevents all self-analysis',
        })
        return voids

    lines = source.splitlines()

    # 1. Functions without docstrings — purpose unknown
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            has_doc = (node.body and isinstance(node.body[0], ast.Expr)
                       and isinstance(node.body[0].value, (ast.Constant, ast.Str)))
            if not has_doc:
                voids.append({
                    'type': 'undocumented_function',
                    'severity': 'medium',
                    'target': node.name,
                    'line': node.lineno,
                    'question': f'what does {node.name}() actually do? no docstring — purpose is a void',
                })

    # 2. Bare except clauses — hiding what it fears
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            voids.append({
                'type': 'swallowed_exception',
                'severity': 'high',
                'line': node.lineno,
                'question': 'bare except on line {} — what failure is being hidden?'.format(node.lineno),
            })

    # 3. Long functions — complexity not decomposed
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, 'end_lineno', node.lineno + 30)
            length = end - node.lineno
            if length > 30:
                voids.append({
                    'type': 'complex_function',
                    'severity': 'medium',
                    'target': node.name,
                    'line': node.lineno,
                    'length': length,
                    'question': f'{node.name}() is {length} lines — what sub-tasks hide inside?',
                })

    # 4. Dead exports — functions nobody calls
    exports = current.get('exports', [])
    coupling = current.get('coupling_score', 0)
    if exports and coupling == 0:
        voids.append({
            'type': 'orphan_module',
            'severity': 'high',
            'question': f'exports {len(exports)} functions but nobody imports this module — ghost or future API?',
        })

    # 5. Magic constants — unexplained decisions
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            if node.value not in (0, 1, -1, 2, 0.0, 1.0, 100, True, False, None):
                # check if it's in an assignment at module level
                parent_line = node.lineno
                if parent_line <= len(lines):
                    line_text = lines[parent_line - 1].strip()
                    if '=' in line_text and not line_text.startswith('#'):
                        # skip if it's a named constant (UPPERCASE)
                        var_name = line_text.split('=')[0].strip()
                        if not var_name.isupper() and not var_name.startswith('_'):
                            voids.append({
                                'type': 'magic_number',
                                'severity': 'low',
                                'line': node.lineno,
                                'value': node.value,
                                'question': f'magic number {node.value} on line {node.lineno} — what does this mean?',
                            })

    # 6. Imports without obvious use — why does it need this?
    imported_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(alias.asname or alias.name.split('.')[-1])
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported_names.add(alias.asname or alias.name)
    # check which imports are actually used in the source
    for name in imported_names:
        # rough check: does the name appear outside import lines?
        used = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith(('import ', 'from ')):
                continue
            if name in stripped:
                used = True
                break
        if not used:
            voids.append({
                'type': 'unused_import',
                'severity': 'medium',
                'target': name,
                'question': f'imports `{name}` but never uses it — vestigial or future dependency?',
            })

    # deduplicate and cap
    seen = set()
    unique = []
    for v in voids:
        key = f"{v['type']}:{v.get('target', '')}:{v.get('line', '')}"
        if key not in seen:
            seen.add(key)
            unique.append(v)
    return unique[:20]  # cap to prevent noise


def _spike_entropy(root: Path, module_stem: str, void_count: int) -> None:
    """Spike a module's entropy when semantic voids are detected."""
    path = root / ENTROPY_MAP
    try:
        data = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    except Exception:
        data = {}

    modules = data.get('top_entropy_modules', [])
    found = False
    for entry in modules:
        if entry.get('module') == module_stem:
            # spike: add void-proportional entropy
            spike = min(ENTROPY_SPIKE * void_count, 0.5)
            entry['avg_entropy'] = min(entry.get('avg_entropy', 0) + spike, 1.0)
            entry['void_spike'] = {
                'ts': datetime.now(timezone.utc).isoformat(),
                'voids': void_count,
                'spike': spike,
            }
            found = True
            break
    if not found and void_count > 0:
        modules.append({
            'module': module_stem,
            'avg_entropy': min(ENTROPY_SPIKE * void_count, 0.5),
            'samples': 0,
            'hedges': 0,
            'void_spike': {
                'ts': datetime.now(timezone.utc).isoformat(),
                'voids': void_count,
                'spike': min(ENTROPY_SPIKE * void_count, 0.5),
            },
        })
    data['top_entropy_modules'] = modules
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')


def _file_context_request(root: Path, module_stem: str, voids: list[dict]) -> None:
    """File a context request — module asking for its own missing context to be filled."""
    path = root / CONTEXT_REQUESTS
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'module': module_stem,
        'void_count': len(voids),
        'questions': [v['question'] for v in voids[:10]],
        'severities': {s: sum(1 for v in voids if v.get('severity') == s)
                       for s in ('critical', 'high', 'medium', 'low')},
        'status': 'pending',
    }
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')


def _grow_module_context(root: Path, module_stem: str, filepath: Path,
                         current: dict, voids: list[dict], drift: dict) -> dict:
    """Grow a module's self-knowledge by recording what it learned on this push.

    Returns the updated context profile. This data feeds back into
    module_identity for richer probe questions and file_consciousness
    for deeper profiles. Context grows monotonically — never shrinks.
    """
    db = _load_db(root)
    profile = db.get(module_stem, {})
    context = profile.get('context', {})

    now = datetime.now(timezone.utc).isoformat()

    # accumulate void history — what the module didn't understand
    void_history = context.get('void_history', [])
    if voids:
        void_history.append({
            'ts': now,
            'count': len(voids),
            'types': list({v['type'] for v in voids}),
            'top_questions': [v['question'] for v in voids[:5]],
        })
    if len(void_history) > 20:
        void_history = void_history[-20:]
    context['void_history'] = void_history

    # track drift trajectory — how much the module changes push to push
    drift_history = context.get('drift_history', [])
    drifted_keys = [k for k, v in drift.items() if v.get('drifted')]
    if drifted_keys:
        drift_history.append({
            'ts': now,
            'drifted': drifted_keys,
            'magnitudes': {k: drift[k]['magnitude'] for k in drifted_keys},
        })
    if len(drift_history) > 20:
        drift_history = drift_history[-20:]
    context['drift_history'] = drift_history

    # semantic growth — new knowledge accumulates
    known_exports = set(context.get('known_exports', []))
    known_exports.update(current.get('exports', []))
    context['known_exports'] = sorted(known_exports)

    known_imports = set(context.get('known_imports', []))
    known_imports.update(current.get('imports', []))
    context['known_imports'] = sorted(known_imports)

    # recurring void patterns — what the module keeps not understanding
    recurring = context.get('recurring_voids', {})
    for v in voids:
        vtype = v['type']
        recurring[vtype] = recurring.get(vtype, 0) + 1
    context['recurring_voids'] = recurring

    # push count — how many times this module has been assessed
    context['push_count'] = context.get('push_count', 0) + 1
    context['last_assessed'] = now

    profile['context'] = context
    db[module_stem] = profile
    _save_db(root, db)
    return context


def assess_on_push(root: Path, changed_files: list[str]) -> dict[str, Any]:
    """Run baseline assessment on all changed modules. The push gate.

    For each changed .py file:
    1. Measure current state (baseline questions)
    2. Compare to genesis snapshot (detect drift)
    3. Find semantic voids (missing context)
    4. If voids found: spike entropy + file context request
    5. Grow module context (accumulate self-knowledge)
    6. Return drift report for prompt injection

    Returns dict with per-module results and summary.
    """
    db = _load_db(root)
    results = {}
    total_drift = 0
    total_voids = 0
    modules_assessed = 0

    for fpath in changed_files:
        filepath = root / fpath if not Path(fpath).is_absolute() else Path(fpath)
        if not filepath.exists() or not filepath.suffix == '.py':
            continue
        if '__pycache__' in str(filepath) or filepath.name.startswith('_tmp_'):
            continue

        stem = filepath.stem
        modules_assessed += 1

        # measure current state
        current = measure_module(filepath, root)

        # load or create genesis snapshot
        entry = db.get(stem, {})
        if 'genesis' not in entry:
            # first push — this IS the genesis
            entry['genesis'] = current.copy()
            entry['genesis']['ts'] = datetime.now(timezone.utc).isoformat()
            entry['genesis_hash'] = current.get('semantic_hash', '')
            db[stem] = entry
            _save_db(root, db)

        genesis = entry['genesis']

        # compute drift from genesis
        drift = _compute_drift(genesis, current)
        drifted_count = sum(1 for v in drift.values() if v.get('drifted'))
        total_drift += drifted_count

        # detect semantic voids
        voids = detect_semantic_voids(filepath, root, current)
        total_voids += len(voids)

        # truth gate: if voids found, spike entropy + request context
        if voids:
            _spike_entropy(root, stem, len(voids))
            _file_context_request(root, stem, voids)

        # grow module context regardless — learning is monotonic
        context = _grow_module_context(root, stem, filepath, current, voids, drift)

        # reload entry after context growth (grow_module_context saves its own state)
        db = _load_db(root)
        entry = db.get(stem, {})

        # update entry with latest measurement
        entry['latest'] = current
        entry['latest']['ts'] = datetime.now(timezone.utc).isoformat()
        entry['drift_count'] = drifted_count
        entry['void_count'] = len(voids)
        entry['state'] = 'drifted' if drifted_count > 0 else 'stable'
        db[stem] = entry
        _save_db(root, db)

        results[stem] = {
            'state': entry['state'],
            'drift': {k: v for k, v in drift.items() if v.get('drifted')},
            'voids': len(voids),
            'void_types': list({v['type'] for v in voids}),
            'top_void': voids[0]['question'] if voids else None,
            'context_growth': context.get('push_count', 0),
        }

    # log drift event
    if modules_assessed > 0:
        log_path = root / DRIFT_LOG
        log_path.parent.mkdir(parents=True, exist_ok=True)
        event = {
            'ts': datetime.now(timezone.utc).isoformat(),
            'modules_assessed': modules_assessed,
            'total_drift': total_drift,
            'total_voids': total_voids,
            'drifted_modules': [s for s, r in results.items() if r['state'] == 'drifted'],
            'void_modules': [s for s, r in results.items() if r['voids'] > 0],
        }
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event) + '\n')

    return {
        'modules_assessed': modules_assessed,
        'total_drift': total_drift,
        'total_voids': total_voids,
        'results': results,
    }


def build_drift_report(root: Path) -> str:
    """Build markdown drift report for prompt injection."""
    db = _load_db(root)
    if not db:
        return ''

    drifted = []
    voided = []
    stable = []
    for stem, entry in sorted(db.items()):
        if not isinstance(entry, dict) or 'genesis' not in entry:
            continue
        state = entry.get('state', 'unknown')
        dc = entry.get('drift_count', 0)
        vc = entry.get('void_count', 0)
        ctx = entry.get('context', {})
        pushes = ctx.get('push_count', 0)

        if state == 'drifted':
            drifted.append((stem, dc, vc, pushes))
        elif vc > 0:
            voided.append((stem, vc, pushes))
        else:
            stable.append(stem)

    lines = ['<!-- pigeon:baseline-drift -->', '## Baseline Drift Report', '']
    lines.append(f'*{len(drifted)} drifted · {len(voided)} have voids · {len(stable)} stable*')
    lines.append('')

    if drifted:
        lines.append('**Drifted from genesis (truth gate triggered):**')
        for stem, dc, vc, pushes in drifted:
            lines.append(f'- `{stem}`: {dc} questions drifted, {vc} voids, {pushes} pushes')
        lines.append('')

    if voided:
        lines.append('**Semantic voids (context growth needed):**')
        for stem, vc, pushes in voided:
            lines.append(f'- `{stem}`: {vc} voids, {pushes} pushes')
        lines.append('')

    # show context requests
    req_path = root / CONTEXT_REQUESTS
    if req_path.exists():
        try:
            recent = []
            for line in req_path.read_text(encoding='utf-8').splitlines()[-5:]:
                entry = json.loads(line)
                recent.append(entry)
            if recent:
                lines.append('**Recent context requests (modules asking for help):**')
                for r in recent:
                    qs = r.get('questions', [])[:2]
                    lines.append(f'- `{r["module"]}` ({r["void_count"]} voids): {qs[0] if qs else "?"}')
                lines.append('')
        except Exception:
            pass

    lines.append('<!-- /pigeon:baseline-drift -->')
    return '\n'.join(lines)


if __name__ == '__main__':
    import sys
    root = Path(__file__).resolve().parent.parent
    # manual run: assess all .py files in src/
    changed = [str(p.relative_to(root)) for p in (root / 'src').glob('*.py')
               if not p.name.startswith('_tmp_')]
    result = assess_on_push(root, changed)
    print(f'Assessed {result["modules_assessed"]} modules')
    print(f'Total drift: {result["total_drift"]}')
    print(f'Total voids: {result["total_voids"]}')
    for stem, r in sorted(result['results'].items()):
        if r['voids'] > 0 or r['state'] == 'drifted':
            print(f'  {stem}: {r["state"]} | {r["voids"]} voids | drift: {list(r["drift"].keys())}')
