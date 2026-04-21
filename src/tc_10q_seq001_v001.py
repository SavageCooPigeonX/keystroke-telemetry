"""tc_10q — 10-question interlink qualification test.

A module is INTERLINKED when it passes all 10 questions.
Questions are deterministic — no LLM, no network.

The 10 questions:
  Q1  syntax_valid      — ast.parse() succeeds
  Q2  cap_compliant     — <= 200 non-empty lines
  Q3  has_docstring     — module-level docstring present
  Q4  api_exported      — at least 1 public function/class
  Q5  imports_resolve   — all src.* imports point to existing files
  Q6  no_bare_except    — no bare `except:` or `except Exception: pass`
  Q7  test_exists       — tests/interlink/test_{base}.py exists
  Q8  test_passes       — that test passes (subprocess)
  Q9  entropy_shed      — confidence declared >= 0.7 in heat map or pulse
  Q10 data_contract     — primary public function returns non-None for safe inputs

Pass all 10 → INTERLINKED. A module stays interlinked across renames
because the test file uses glob-based imports (see interlinker.py).
"""
# ── telemetry:pulse ──
# EDIT_TS:   2026-04-21T04:35:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  Q10 scenario-aware via edit intent
# EDIT_AUTHOR: copilot
# EDIT_STATE: harvested
# ── /pulse ──
from __future__ import annotations
import ast
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
INTERLINK_TESTS = ROOT / 'tests' / 'interlink'
HEAT_MAP = ROOT / 'file_heat_map.json'
RESULTS_LOG = ROOT / 'logs' / 'tc_10q_results.jsonl'
ENTROPY_THRESHOLD = 0.7


# ── helpers ───────────────────────────────────────────────────────────────────

def _base_stem(p: Path) -> str:
    return re.sub(r'_seq\d+.*$', '', p.stem) or p.stem


def _count_lines(p: Path) -> int:
    try:
        return sum(1 for ln in p.read_text(encoding='utf-8', errors='ignore').splitlines() if ln.strip())
    except Exception:
        return 9999


def _parse(p: Path):
    return ast.parse(p.read_text(encoding='utf-8', errors='ignore'), filename=str(p))


def _public_api(tree) -> list[str]:
    names = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not node.name.startswith('_'):
                names.append(node.name)
    return names


def _shed_confidence(stem: str) -> float | None:
    """Look for shed confidence in file_heat_map.json or pulse block."""
    if HEAT_MAP.exists():
        try:
            hm = json.loads(HEAT_MAP.read_text(encoding='utf-8'))
            e = hm.get(stem, {})
            if isinstance(e, dict):
                c = e.get('confidence') or e.get('shed_confidence')
                if c is not None:
                    return float(c)
        except Exception:
            pass
    # check pulse block in file
    src_matches = sorted((ROOT / 'src').glob(f'{stem}*.py'), key=lambda p: len(p.name))
    if src_matches:
        text = src_matches[0].read_text(encoding='utf-8', errors='ignore')
        m = re.search(r'EDIT_HASH:\s*([\d.]+)', text)
        if m:
            try:
                v = float(m.group(1))
                if 0 <= v <= 1:
                    return v
            except ValueError:
                pass
    return None


def _imports_resolve(tree, root: Path) -> list[str]:
    broken = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith('src.'):
            parts = node.module.split('.')
            parent = root / '/'.join(parts[:-1])
            stem = parts[-1]
            if parent.exists():
                if not list(parent.glob(f'{stem}*.py')):
                    broken.append(node.module)
    return broken


def _has_bare_except(tree) -> bool:
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                return True
            # `except Exception: pass` (single pass body)
            if (isinstance(node.type, ast.Name) and node.type.id == 'Exception'
                    and len(node.body) == 1
                    and isinstance(node.body[0], ast.Pass)):
                return True
    return False


# ── the 10 questions ──────────────────────────────────────────────────────────

def run_10q(filepath: Path) -> dict:
    """Run all 10 questions for a module. Returns full result dict."""
    base = _base_stem(filepath)
    now = datetime.now(timezone.utc).isoformat()
    answers: dict[str, bool] = {}
    notes: dict[str, str] = {}

    # Q1 — syntax valid
    try:
        tree = _parse(filepath)
        answers['Q1_syntax_valid'] = True
    except SyntaxError as e:
        answers['Q1_syntax_valid'] = False
        notes['Q1'] = f'line {e.lineno}: {e.msg}'
        tree = None

    # Q2 — cap compliant
    lines = _count_lines(filepath)
    answers['Q2_cap_compliant'] = lines <= 200
    notes['Q2'] = f'{lines} lines'

    # Q3 — has docstring
    if tree:
        ds = ast.get_docstring(tree)
        answers['Q3_has_docstring'] = bool(ds and len(ds.strip()) > 10)
    else:
        answers['Q3_has_docstring'] = False

    # Q4 — api exported
    if tree:
        api = _public_api(tree)
        answers['Q4_api_exported'] = len(api) > 0
        notes['Q4'] = f'{len(api)} public names'
    else:
        answers['Q4_api_exported'] = False
        api = []

    # Q5 — imports resolve
    if tree:
        broken = _imports_resolve(tree, ROOT)
        answers['Q5_imports_resolve'] = len(broken) == 0
        if broken:
            notes['Q5'] = f'broken: {broken[:3]}'
    else:
        answers['Q5_imports_resolve'] = False

    # Q6 — no bare except
    if tree:
        answers['Q6_no_bare_except'] = not _has_bare_except(tree)
    else:
        answers['Q6_no_bare_except'] = False

    # Q7 — test exists
    test_path = INTERLINK_TESTS / f'test_{base}.py'
    answers['Q7_test_exists'] = test_path.exists()

    # Q8 — test passes
    if answers['Q7_test_exists']:
        try:
            r = subprocess.run(
                [sys.executable, str(test_path)],
                capture_output=True, text=True, encoding='utf-8', errors='replace',
                cwd=str(ROOT), timeout=15,
            )
            answers['Q8_test_passes'] = r.returncode == 0
            if r.returncode != 0:
                notes['Q8'] = (r.stderr + r.stdout)[:200]
        except subprocess.TimeoutExpired:
            answers['Q8_test_passes'] = False
            notes['Q8'] = 'timeout'
    else:
        answers['Q8_test_passes'] = False

    # Q9 — entropy shed
    conf = _shed_confidence(base)
    answers['Q9_entropy_shed'] = conf is not None and conf >= ENTROPY_THRESHOLD
    notes['Q9'] = f'confidence={conf}'

    # Q10 — data contract: primary function returns non-None + scenario note from last edit intent
    answers['Q10_data_contract'] = False
    notes['Q10_scenario'] = ''
    if tree and api:
        primary = api[0]
        fn_nodes = [n for n in ast.iter_child_nodes(tree)
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and n.name == primary]
        if fn_nodes:
            fn_args = [a.arg for a in fn_nodes[0].args.args if a.arg != 'self']
            if not fn_args or fn_args == ['root']:
                try:
                    import importlib.util as _ilu
                    matches = sorted((ROOT / 'src').glob(f'{base}*.py'), key=lambda p: len(p.name))
                    if matches:
                        spec = _ilu.spec_from_file_location(base, matches[0])
                        mod = _ilu.module_from_spec(spec)
                        spec.loader.exec_module(mod)
                        fn = getattr(mod, primary, None)
                        if callable(fn):
                            result = fn(ROOT) if fn_args == ['root'] else fn()
                            answers['Q10_data_contract'] = result is not None
                            # attach intent scenario from last edit pulse block
                            src_text = matches[0].read_text('utf-8', errors='ignore')
                            why_m = re.search(r'# EDIT_WHY:\s*(.+)', src_text)
                            edit_why = why_m.group(1).strip() if why_m else ''
                            if edit_why and edit_why not in ('None', ''):
                                notes['Q10_scenario'] = f'last edit: {edit_why}'
                            if not notes['Q10_scenario']:
                                notes['Q10_scenario'] = f'{primary}() returned {type(result).__name__}'
                except Exception as e:
                    notes['Q10'] = str(e)[:100]

    passed = sum(answers.values())
    interlinked = passed == 10
    return {
        'ts': now,
        'module': base,
        'path': str(filepath.resolve().relative_to(ROOT)),
        'score': f'{passed}/10',
        'interlinked': interlinked,
        'answers': answers,
        'notes': {k: v for k, v in notes.items() if v},
    }


def qualify_module(filepath: Path, write_log: bool = True) -> dict:
    """Run 10Q and optionally append to results log."""
    result = run_10q(filepath)
    if write_log:
        RESULTS_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(RESULTS_LOG, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    return result


def qualify_all(scope: str = 'src', max_files: int = 50) -> list[dict]:
    """Run 10Q on all modules in scope. Returns list of results."""
    results = []
    src = ROOT / scope
    for py in sorted(src.glob('*.py'))[:max_files]:
        if py.name.startswith('_'):
            continue
        results.append(qualify_module(py, write_log=True))
    return results


def summary_report(results: list[dict]) -> str:
    """Build a compact summary of 10Q results."""
    interlinked = [r for r in results if r['interlinked']]
    near = [r for r in results if not r['interlinked'] and int(r['score'].split('/')[0]) >= 8]
    lines = [
        f'10Q Results: {len(interlinked)}/{len(results)} INTERLINKED',
        f'Near ({len(near)} at 8-9/10): {", ".join(r["module"] for r in near[:5])}',
        '',
        'Blocking questions (most common failures):',
    ]
    q_fails: dict[str, int] = {}
    for r in results:
        for q, v in r['answers'].items():
            if not v:
                q_fails[q] = q_fails.get(q, 0) + 1
    for q, n in sorted(q_fails.items(), key=lambda x: -x[1])[:5]:
        lines.append(f'  {q}: {n} modules failing')
    return '\n'.join(lines)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='10-question interlink test')
    p.add_argument('module', nargs='?', help='module file or base name to test')
    p.add_argument('--all', action='store_true', help='Qualify all src modules')
    p.add_argument('--max', type=int, default=20)
    args = p.parse_args()

    if args.all:
        results = qualify_all(max_files=args.max)
        print(summary_report(results))
    elif args.module:
        # allow passing just base name or full path
        path = Path(args.module)
        if not path.exists():
            matches = sorted((ROOT / 'src').glob(f'{args.module}*.py'), key=lambda p: len(p.name))
            path = matches[0] if matches else path
        result = qualify_module(path)
        print(json.dumps(result, indent=2))
    else:
        p.print_help()
