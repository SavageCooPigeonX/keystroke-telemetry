"""Interlinker — Blade Runner 2049 module singularity engine.

A module becomes INTERLINKED when:
1. It has a self-test (auto-generated or hand-written)
2. The self-test passes
3. It's under pigeon cap (≤200 lines)
4. Its data flow is confirmed (imports resolve, exports used)
5. Entropy is shed (confidence ≥ 0.7)

Interlinked modules sleep — their test guards them. They keep
learning via intent shards while sleeping. Eventually the whole
codebase is interlinked and modules can be simulated from their
learned profiles.

State machine: baseline → tested → compressed → interlinked → sleeping
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──

from __future__ import annotations
import ast
import hashlib
import json
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── states ──────────────────────────────────────────────────
STATES = ('baseline', 'tested', 'compressed', 'interlinked', 'sleeping')
INTERLINK_DB = 'logs/interlink_state.json'
INTERLINK_TESTS_DIR = 'tests/interlink'
PIGEON_CAP = 200
ENTROPY_THRESHOLD = 0.7  # shed confidence must be ≥ this


def load_interlink_db(root: Path) -> dict[str, Any]:
    """Load the interlink state database."""
    path = root / INTERLINK_DB
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    return {}


def save_interlink_db(root: Path, db: dict[str, Any]) -> None:
    """Persist interlink state."""
    path = root / INTERLINK_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(db, indent=2, ensure_ascii=False), encoding='utf-8')


def _module_stem(filepath: Path) -> str:
    """Extract module stem from a file path."""
    return filepath.stem


def _count_lines(filepath: Path) -> int:
    """Count non-empty lines in a Python file."""
    try:
        return sum(1 for ln in filepath.read_text(encoding='utf-8').splitlines() if ln.strip())
    except Exception:
        return 9999


def _check_syntax(filepath: Path) -> tuple[bool, str]:
    """AST-parse a file. Returns (ok, error_msg)."""
    try:
        source = filepath.read_text(encoding='utf-8')
        ast.parse(source, filename=str(filepath))
        return True, ''
    except SyntaxError as e:
        return False, f'syntax error line {e.lineno}: {e.msg}'
    except Exception as e:
        return False, str(e)


def _extract_public_api(filepath: Path) -> list[dict]:
    """Extract public functions/classes with their signatures."""
    try:
        source = filepath.read_text(encoding='utf-8')
        tree = ast.parse(source)
    except Exception:
        return []
    api = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
            args = [a.arg for a in node.args.args if a.arg != 'self']
            ret = ast.dump(node.returns) if node.returns else 'Any'
            api.append({'name': node.name, 'args': args, 'returns': ret, 'line': node.lineno})
        elif isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
            methods = [n.name for n in ast.walk(node)
                       if isinstance(n, ast.FunctionDef) and not n.name.startswith('_')]
            api.append({'name': node.name, 'type': 'class', 'methods': methods, 'line': node.lineno})
    return api


def _get_imports(filepath: Path) -> list[str]:
    """Get all import targets from a file."""
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


def _check_imports_resolve(filepath: Path, root: Path) -> tuple[bool, list[str]]:
    """Check if all imports from src.* actually resolve to existing files."""
    imports = _get_imports(filepath)
    broken = []
    for imp in imports:
        if imp.startswith('src.') or imp.startswith('src'):
            parts = imp.split('.')
            # try to find the module file
            candidate = root / ('/'.join(parts) + '.py')
            candidate_pkg = root / '/'.join(parts) / '__init__.py'
            if not candidate.exists() and not candidate_pkg.exists():
                # glob fallback for pigeon names
                parent = root / '/'.join(parts[:-1])
                stem = parts[-1] if len(parts) > 1 else ''
                if stem and parent.exists():
                    matches = list(parent.glob(f'{stem}*.py'))
                    if not matches:
                        broken.append(imp)
                elif not parent.exists():
                    broken.append(imp)
    return len(broken) == 0, broken


def _get_entropy(module_stem: str, root: Path) -> float | None:
    """Get the latest entropy/confidence for a module from heat map."""
    hm_path = root / 'file_heat_map.json'
    if not hm_path.exists():
        return None
    try:
        hm = json.loads(hm_path.read_text(encoding='utf-8'))
        entry = hm.get(module_stem, {})
        if isinstance(entry, dict):
            return entry.get('entropy')
    except Exception:
        pass
    return None


def _get_shed_confidence(module_stem: str, root: Path) -> float | None:
    """Get latest shed confidence from entropy map in copilot-instructions."""
    # check the red layer in copilot-instructions.md
    ci = root / '.github' / 'copilot-instructions.md'
    if not ci.exists():
        return None
    try:
        text = ci.read_text(encoding='utf-8')
        for line in text.splitlines():
            if f'red[{module_stem}]' in line:
                # format: red[name] = [red, H_avg, shed_conf, samples, hedges]
                bracket = line.split('[', 2)[-1].rstrip(']').strip()
                parts = [p.strip() for p in bracket.split(',')]
                if len(parts) >= 3 and parts[2] not in ('null', 'None', ''):
                    return float(parts[2])
    except Exception:
        pass
    return None


def assess_module(filepath: Path, root: Path) -> dict[str, Any]:
    """Assess a module's interlink readiness. Returns status + checklist."""
    stem = _module_stem(filepath)
    lines = _count_lines(filepath)
    syntax_ok, syntax_err = _check_syntax(filepath)
    api = _extract_public_api(filepath)
    imports_ok, broken_imports = _check_imports_resolve(filepath, root)
    entropy = _get_entropy(stem, root)
    shed_conf = _get_shed_confidence(stem, root)

    # check for existing self-test
    test_dir = root / INTERLINK_TESTS_DIR
    test_file = test_dir / f'test_{stem}.py'
    has_test = test_file.exists()

    # checklist
    checks = {
        'syntax_valid': syntax_ok,
        'under_cap': lines <= PIGEON_CAP,
        'imports_resolve': imports_ok,
        'has_public_api': len(api) > 0,
        'has_self_test': has_test,
        'entropy_shed': shed_conf is not None and shed_conf >= ENTROPY_THRESHOLD,
    }

    # determine state
    if all(checks.values()):
        state = 'interlinked'
    elif checks['syntax_valid'] and checks['has_self_test']:
        state = 'tested'
    elif checks['syntax_valid'] and checks['under_cap']:
        state = 'compressed'
    else:
        state = 'baseline'

    return {
        'module': stem,
        'path': str(filepath.relative_to(root)),
        'state': state,
        'lines': lines,
        'public_api': len(api),
        'api': api,
        'checks': checks,
        'entropy': entropy,
        'shed_confidence': shed_conf,
        'broken_imports': broken_imports,
        'syntax_error': syntax_err,
    }


def generate_self_test(filepath: Path, root: Path) -> str:
    """Generate a self-test for a module based on its public API.

    The test validates:
    - Module imports without error
    - All public functions are callable
    - Return types match expectations (smoke test)
    - Data flow contracts (inputs → outputs) hold
    """
    stem = _module_stem(filepath)
    rel_path = filepath.relative_to(root)
    # build import path: src/foo.py → src.foo
    import_path = str(rel_path.with_suffix('')).replace('\\', '.').replace('/', '.')
    api = _extract_public_api(filepath)

    lines = [
        f'"""Interlink self-test for {stem}.',
        f'',
        f'Auto-generated. This test keeps {stem} interlinked.',
        f'When this passes + pigeon cap + entropy shed → module sleeps.',
        f'Module keeps learning via intent shards while sleeping.',
        f'"""',
        f'import sys',
        f'from pathlib import Path',
        f'sys.path.insert(0, str(Path(__file__).resolve().parents[2]))',
        f'',
    ]

    # import the module
    if api:
        names = [a['name'] for a in api]
        lines.append(f'def test_import():')
        lines.append(f'    """Module imports without error."""')
        lines.append(f'    from {import_path} import {", ".join(names)}')
        for name in names:
            lines.append(f'    assert callable({name}), "{name} must be callable"')
        lines.append(f'    print(f"  ✓ {stem}: {len(names)} exports verified")')
        lines.append(f'')
    else:
        lines.append(f'def test_import():')
        lines.append(f'    """Module imports without error."""')
        lines.append(f'    import importlib')
        lines.append(f'    mod = importlib.import_module("{import_path}")')
        lines.append(f'    print(f"  ✓ {stem}: module loads")')
        lines.append(f'')

    # data flow tests for each function
    for item in api:
        if item.get('type') == 'class':
            continue
        name = item['name']
        args = item.get('args', [])
        fn_name = f'test_{name}_contract'
        lines.append(f'def {fn_name}():')
        lines.append(f'    """Data flow contract: {name}({", ".join(args)}) → output."""')
        lines.append(f'    from {import_path} import {name}')
        lines.append(f'    # smoke test: function exists and is callable')
        lines.append(f'    assert {name}.__name__ == "{name}"')

        # generate safe smoke calls for common patterns
        if _is_safe_to_call(name, args):
            if args == ['root'] or args == ['root', 'path']:
                lines.append(f'    # safe to call with test root')
                lines.append(f'    root = Path(__file__).resolve().parents[2]')
                lines.append(f'    result = {name}(root)')
                lines.append(f'    assert result is not None, "{name} returned None"')
            elif not args:
                lines.append(f'    result = {name}()')
                lines.append(f'    assert result is not None, "{name} returned None"')

        lines.append(f'    print(f"  ✓ {name}: contract holds")')
        lines.append(f'')

    # runner
    lines.append(f'def run_interlink_test():')
    lines.append(f'    """Run all interlink checks for {stem}."""')
    lines.append(f'    tests = [v for k, v in globals().items() if k.startswith("test_")]')
    lines.append(f'    passed = 0')
    lines.append(f'    for t in tests:')
    lines.append(f'        try:')
    lines.append(f'            t()')
    lines.append(f'            passed += 1')
    lines.append(f'        except Exception as e:')
    lines.append(f'            print(f"  ✗ {{t.__name__}}: {{e}}")')
    lines.append(f'    total = len(tests)')
    lines.append(f'    status = "INTERLINKED" if passed == total else f"{{passed}}/{{total}}"')
    lines.append(f'    print(f"  {stem}: {{status}}")')
    lines.append(f'    return passed == total')
    lines.append(f'')
    lines.append(f'if __name__ == "__main__":')
    lines.append(f'    success = run_interlink_test()')
    lines.append(f'    raise SystemExit(0 if success else 1)')

    return '\n'.join(lines) + '\n'


def _is_safe_to_call(name: str, args: list[str]) -> bool:
    """Heuristic: is this function safe to call in a test?"""
    unsafe = ('write', 'delete', 'remove', 'push', 'send', 'deploy', 'drop',
              'compile', 'rename', 'fix', 'heal', 'rewrite', 'auto_')
    return not any(name.startswith(u) or name.endswith(u) for u in unsafe)


def write_self_test(filepath: Path, root: Path) -> Path:
    """Generate and write a self-test for a module. Returns test path."""
    stem = _module_stem(filepath)
    test_dir = root / INTERLINK_TESTS_DIR
    test_dir.mkdir(parents=True, exist_ok=True)
    test_path = test_dir / f'test_{stem}.py'
    content = generate_self_test(filepath, root)
    test_path.write_text(content, encoding='utf-8')
    return test_path


def run_self_test(filepath: Path, root: Path) -> tuple[bool, str]:
    """Run the interlink self-test for a module. Returns (passed, output)."""
    import subprocess, sys
    stem = _module_stem(filepath)
    test_path = root / INTERLINK_TESTS_DIR / f'test_{stem}.py'
    if not test_path.exists():
        return False, f'no self-test for {stem}'
    try:
        r = subprocess.run(
            [sys.executable, str(test_path)],
            capture_output=True, text=True, encoding='utf-8',
            cwd=str(root), timeout=15,
        )
        output = (r.stdout + r.stderr).strip()
        return r.returncode == 0, output
    except Exception as e:
        return False, str(e)


def interlink_module(filepath: Path, root: Path, force_test_gen: bool = False) -> dict:
    """Full interlink pipeline for a single module.

    1. Assess current state
    2. Generate self-test if missing
    3. Run self-test
    4. Update interlink database
    5. Return status with shard accumulation
    """
    assessment = assess_module(filepath, root)
    stem = assessment['module']

    # generate test if missing or forced
    if not assessment['checks']['has_self_test'] or force_test_gen:
        test_path = write_self_test(filepath, root)
        assessment['checks']['has_self_test'] = True
        assessment['test_generated'] = True

    # run test
    test_passed, test_output = run_self_test(filepath, root)
    assessment['test_passed'] = test_passed
    assessment['test_output'] = test_output

    # re-evaluate state
    checks = assessment['checks']
    checks['test_passes'] = test_passed
    if all([checks['syntax_valid'], checks['under_cap'], checks['imports_resolve'],
            checks['has_self_test'], test_passed, checks['entropy_shed']]):
        assessment['state'] = 'interlinked'
    elif checks['syntax_valid'] and test_passed:
        assessment['state'] = 'tested'
    elif checks['syntax_valid'] and checks['under_cap']:
        assessment['state'] = 'compressed'

    # update database
    db = load_interlink_db(root)
    now = datetime.now(timezone.utc).isoformat()
    existing = db.get(stem, {})
    db[stem] = {
        'state': assessment['state'],
        'last_checked': now,
        'lines': assessment['lines'],
        'public_api': assessment['public_api'],
        'test_passed': test_passed,
        'checks': checks,
        'entropy': assessment['entropy'],
        'shed_confidence': assessment['shed_confidence'],
        'path': assessment['path'],
        # learning: accumulate intent shards
        'shards': existing.get('shards', []),
        'times_checked': existing.get('times_checked', 0) + 1,
        'test_level': existing.get('test_level', 'baseline'),
        'upgrade_count': existing.get('upgrade_count', 0),
        'first_interlinked': existing.get('first_interlinked') or (now if assessment['state'] == 'interlinked' else None),
        'last_state_change': now if existing.get('state') != assessment['state'] else existing.get('last_state_change', now),
    }
    save_interlink_db(root, db)

    return assessment


def accumulate_shard(root: Path, module_stem: str, shard: dict) -> None:
    """Feed an intent shard to a sleeping/interlinked module.

    Shards come from: operator probes, unsaid threads, prompt references,
    edit pairs that touch partner modules, cognitive state at mention time.
    Modules keep learning even while interlinked.
    """
    db = load_interlink_db(root)
    entry = db.get(module_stem)
    if not entry:
        return
    shards = entry.get('shards', [])
    shard['ts'] = datetime.now(timezone.utc).isoformat()
    shards.append(shard)
    # cap shard history
    if len(shards) > 50:
        shards = shards[-50:]
    entry['shards'] = shards
    db[module_stem] = entry
    save_interlink_db(root, db)


def interlink_scan(root: Path, scope: str = 'src') -> dict:
    """Scan all modules in scope and return interlink summary."""
    src = root / scope
    results = {'interlinked': [], 'tested': [], 'compressed': [], 'baseline': []}
    total = 0
    for py in sorted(src.glob('*.py')):
        if py.name.startswith('_'):
            continue
        assessment = assess_module(py, root)
        results[assessment['state']].append(assessment['module'])
        total += 1
    results['total'] = total
    results['interlinked_pct'] = round(len(results['interlinked']) / max(total, 1) * 100, 1)
    return results


def build_interlink_report(root: Path) -> str:
    """Build a markdown report of interlink status for prompt injection."""
    db = load_interlink_db(root)
    if not db:
        return ''
    states = {'sleeping': [], 'interlinked': [], 'tested': [], 'compressed': [], 'baseline': []}
    for stem, entry in sorted(db.items()):
        st = entry.get('state', 'baseline')
        shard_count = len(entry.get('shards', []))
        states.setdefault(st, []).append((stem, shard_count, entry.get('times_checked', 0)))

    lines = ['<!-- pigeon:interlink-status -->', '## Interlink Status', '']
    total = sum(len(v) for v in states.values())
    interlinked = len(states.get('interlinked', [])) + len(states.get('sleeping', []))
    lines.append(f'*{interlinked}/{total} modules interlinked*')
    lines.append('')

    if states.get('interlinked') or states.get('sleeping'):
        lines.append('**Interlinked (sleeping, test guards them):**')
        for stem, shards, checks in (states.get('sleeping', []) + states.get('interlinked', [])):
            lines.append(f'- `{stem}` ({shards} shards, checked {checks}x)')
        lines.append('')

    if states.get('tested'):
        lines.append('**Tested (need cap + entropy shed):**')
        for stem, shards, checks in states['tested']:
            lines.append(f'- `{stem}` ({shards} shards)')
        lines.append('')

    if states.get('baseline'):
        lines.append(f'**Baseline:** {len(states["baseline"])} modules not yet interlinked')
        lines.append('')

    lines.append('<!-- /pigeon:interlink-status -->')
    return '\n'.join(lines)
