"""interlink_debugger — the sim debugs its own tests.

When an interlink test fails, this module:
1. Classifies the failure (import_error | assertion_error | logic_error | crash)
2. For import_error → regenerate test with current glob path, re-run
3. For assertion_error → log to interlink_debug.jsonl, mark for Gemini upgrade
4. For crash → log trace, skip this cycle

Called from: post-commit hook + `py -m src.interlink_debugger`
Output: logs/interlink_debug.jsonl, tests/interlink/ (updated tests)
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: auto
# EDIT_WHY:  initial build - self-debug loop
# EDIT_AUTHOR: copilot
# EDIT_STATE: harvested
# ── /pulse ──
from __future__ import annotations
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
DEBUG_LOG = ROOT / 'logs' / 'interlink_debug.jsonl'
INTERLINK_TESTS = ROOT / 'tests' / 'interlink'
MAX_MODULES_PER_RUN = 8  # cap to keep post-commit fast


# ── failure classification ────────────────────────────────────────────────────

def classify_failure(stderr: str, stdout: str) -> tuple[str, str]:
    """Return (failure_type, detail).

    Types: import_error | assertion_error | logic_error | timeout | unknown
    """
    combined = stderr + stdout
    if 'ModuleNotFoundError' in combined or 'ImportError' in combined:
        # extract the bad module name
        m = re.search(r"No module named '([^']+)'", combined)
        detail = m.group(1) if m else 'unknown module'
        return 'import_error', detail
    if 'AssertionError' in combined:
        m = re.search(r'AssertionError: (.+)', combined)
        detail = m.group(1) if m else 'assertion failed'
        return 'assertion_error', detail
    if 'SyntaxError' in combined:
        return 'syntax_error', combined[:200]
    if combined.strip():
        return 'logic_error', combined[:200]
    return 'unknown', ''


# ── per-test repair ────────────────────────────────────────────────────────────

def _run_test(test_path: Path) -> tuple[bool, str, str]:
    """Run a single test file. Returns (passed, stdout, stderr)."""
    try:
        r = subprocess.run(
            [sys.executable, str(test_path)],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            cwd=str(ROOT), timeout=15,
        )
        return r.returncode == 0, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return False, '', 'timeout'
    except Exception as e:
        return False, '', str(e)


def _find_module_for_test(test_path: Path) -> Path | None:
    """Given tests/interlink/test_foo.py, find src/foo*.py."""
    base = test_path.stem.removeprefix('test_')
    matches = sorted((ROOT / 'src').glob(f'{base}*.py'), key=lambda p: len(p.name))
    return matches[0] if matches else None


def debug_one(test_path: Path) -> dict:
    """Debug a single failing test. Returns a debug record."""
    now = datetime.now(timezone.utc).isoformat()
    passed, stdout, stderr = _run_test(test_path)
    if passed:
        return {'ts': now, 'test': test_path.name, 'result': 'pass', 'action': 'none'}

    failure_type, detail = classify_failure(stderr, stdout)
    record: dict = {
        'ts': now,
        'test': test_path.name,
        'failure_type': failure_type,
        'detail': detail,
        'result': 'fail',
        'action': 'none',
    }

    if failure_type == 'import_error':
        # Regenerate the test with the correct current path
        module_path = _find_module_for_test(test_path)
        if module_path:
            try:
                from src.interlinker_seq001_v001 import write_self_test, run_self_test
                write_self_test(module_path, ROOT)
                repassed, reout = run_self_test(module_path, ROOT)
                record['action'] = 'regenerated'
                record['rerun_passed'] = repassed
                record['rerun_output'] = reout[:300]
                if repassed:
                    record['result'] = 'fixed'
            except Exception as e:
                record['action'] = 'regen_failed'
                record['regen_error'] = str(e)
        else:
            record['action'] = 'module_not_found'

    elif failure_type == 'assertion_error':
        # Mark for Gemini upgrade — interlinker_upgrade picks these up
        record['action'] = 'queued_for_upgrade'

    return record


# ── batch runner ──────────────────────────────────────────────────────────────

def debug_batch(max_modules: int = MAX_MODULES_PER_RUN) -> dict:
    """Debug a batch of failing tests. Prioritize import_errors first."""
    if not INTERLINK_TESTS.exists():
        return {'fixed': 0, 'still_failing': 0, 'skipped': 0}

    all_tests = sorted(INTERLINK_TESTS.glob('test_*.py'))

    # quick pre-screen — only process tests that are currently failing
    failing = []
    for t in all_tests:
        passed, _, _ = _run_test(t)
        if not passed:
            failing.append(t)
        if len(failing) >= max_modules * 2:
            break

    # sort: import_errors first (cheapest to fix)
    def priority(t: Path) -> int:
        _, stdout, stderr = _run_test(t)
        ft, _ = classify_failure(stderr, stdout)
        return 0 if ft == 'import_error' else 1

    failing.sort(key=priority)
    to_process = failing[:max_modules]

    fixed = 0
    still_failing = 0
    records = []
    for t in to_process:
        rec = debug_one(t)
        records.append(rec)
        if rec['result'] == 'fixed':
            fixed += 1
        elif rec['result'] == 'fail':
            still_failing += 1

    # append to debug log
    DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(DEBUG_LOG, 'a', encoding='utf-8') as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')

    summary = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'processed': len(to_process),
        'fixed': fixed,
        'still_failing': still_failing,
        'total_failing': len(failing),
    }
    return summary


# ── status report ─────────────────────────────────────────────────────────────

def status_report(root: Path = ROOT) -> str:
    """Quick markdown summary of interlink test health."""
    all_tests = sorted(INTERLINK_TESTS.glob('test_*.py'))
    if not all_tests:
        return 'no interlink tests found'

    passed_n, failed_n = 0, 0
    failure_types: dict[str, int] = {}
    for t in all_tests:
        ok, stdout, stderr = _run_test(t)
        if ok:
            passed_n += 1
        else:
            failed_n += 1
            ft, _ = classify_failure(stderr, stdout)
            failure_types[ft] = failure_types.get(ft, 0) + 1

    total = passed_n + failed_n
    lines = [
        f'**Interlink tests: {passed_n}/{total} passing**',
        '',
    ]
    if failure_types:
        lines.append('Failures by type:')
        for ft, n in sorted(failure_types.items(), key=lambda x: -x[1]):
            lines.append(f'- {ft}: {n}')
    return '\n'.join(lines)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Interlink self-debugger')
    p.add_argument('--status', action='store_true', help='Print status report')
    p.add_argument('--fix', action='store_true', help='Run debug batch (fix import errors)')
    p.add_argument('--max', type=int, default=MAX_MODULES_PER_RUN)
    args = p.parse_args()

    if args.status:
        print(status_report())
    elif args.fix:
        result = debug_batch(max_modules=args.max)
        print(f"processed={result['processed']} fixed={result['fixed']} still_failing={result['still_failing']}")
    else:
        p.print_help()
