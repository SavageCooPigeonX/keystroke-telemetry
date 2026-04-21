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
# EDIT_TS:   2026-04-21T04:35:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  intent-aware prioritization + context
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


# ── intent context ───────────────────────────────────────────────────────────

def _current_intent(root: Path = ROOT) -> dict:
    """Read the latest operator intent from prompt_journal + intent_jobs.

    Returns: {intent_text, intent_tokens, deleted_words, cognitive_state}
    """
    result = {'intent_text': '', 'intent_tokens': set(), 'deleted_words': [], 'cognitive_state': 'unknown'}
    # try prompt_journal first — most current
    pj = root / 'logs' / 'prompt_journal.jsonl'
    if pj.exists():
        try:
            lines = pj.read_text('utf-8', errors='ignore').strip().splitlines()
            if lines:
                e = json.loads(lines[-1])
                result['intent_text'] = (e.get('intent') or e.get('msg') or '')[:200]
                result['deleted_words'] = e.get('deleted_words', [])
                if e.get('signals'):
                    result['cognitive_state'] = e['signals'].get('cognitive_state', 'unknown')
        except Exception:
            pass
    # supplement with pending intent_jobs
    ij = root / 'logs' / 'intent_jobs.jsonl'
    if ij.exists() and not result['intent_text']:
        try:
            lines = ij.read_text('utf-8', errors='ignore').strip().splitlines()
            pending = [json.loads(l) for l in lines if '"pending"' in l]
            if pending:
                result['intent_text'] = pending[-1].get('intent_text', '')
        except Exception:
            pass
    # tokenize intent text
    result['intent_tokens'] = set(re.findall(r'[a-z][a-z0-9_]+', result['intent_text'].lower()))
    return result


def _intent_for_module(base: str, root: Path = ROOT) -> dict:
    """Find the last edit intent for a module from edit_pairs + pulse block.

    Returns: {intent_text, edit_why, deleted_words, last_touch_ts}
    """
    result = {'intent_text': '', 'edit_why': '', 'deleted_words': [], 'last_touch_ts': ''}
    # check pulse block in source file
    matches = sorted((root / 'src').glob(f'{base}*.py'), key=lambda p: len(p.name))
    if matches:
        try:
            text = matches[0].read_text('utf-8', errors='ignore')
            why = re.search(r'# EDIT_WHY:\s*(.+)', text)
            ts = re.search(r'# EDIT_TS:\s*(.+)', text)
            if why and why.group(1).strip() not in ('None', ''):
                result['edit_why'] = why.group(1).strip()
            if ts and ts.group(1).strip() not in ('None', ''):
                result['last_touch_ts'] = ts.group(1).strip()
        except Exception:
            pass
    # check edit_pairs for richer intent
    ep = root / 'logs' / 'edit_pairs.jsonl'
    if ep.exists():
        try:
            lines = ep.read_text('utf-8', errors='ignore').strip().splitlines()
            for line in reversed(lines):
                e = json.loads(line)
                f = e.get('file', '')
                if base in f:
                    result['intent_text'] = e.get('prompt_intent') or e.get('prompt_msg', '')[:100]
                    result['deleted_words'] = e.get('deleted_words', [])
                    result['last_touch_ts'] = e.get('edit_ts', result['last_touch_ts'])
                    break
        except Exception:
            pass
    if not result['intent_text'] and result['edit_why']:
        result['intent_text'] = result['edit_why']
    return result


def _intent_score(base: str, current_intent: dict) -> float:
    """Score how relevant this module is to the current operator intent (0-1).

    Higher = more likely to be what the operator is actively debugging.
    """
    current_tokens = current_intent.get('intent_tokens', set())
    if not current_tokens:
        return 0.0
    # match against module base name tokens
    mod_tokens = set(re.findall(r'[a-z][a-z0-9]+', base.lower()))
    overlap = len(current_tokens & mod_tokens)
    if overlap:
        return min(1.0, overlap / max(len(current_tokens), 1) * 2)
    # also check edit_why of the module
    mod_intent = _intent_for_module(base)
    why_tokens = set(re.findall(r'[a-z][a-z0-9_]+', mod_intent.get('edit_why', '').lower()))
    why_overlap = len(current_tokens & why_tokens)
    return min(0.8, why_overlap / max(len(current_tokens), 1))


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


def debug_one(test_path: Path, intent_ctx: dict | None = None) -> dict:
    """Debug a single failing test. Returns a debug record enriched with intent."""
    now = datetime.now(timezone.utc).isoformat()
    passed, stdout, stderr = _run_test(test_path)
    base = test_path.stem.removeprefix('test_')
    mod_intent = _intent_for_module(base)
    if intent_ctx is None:
        intent_ctx = _current_intent()
    relevance = _intent_score(base, intent_ctx)

    if passed:
        return {'ts': now, 'test': test_path.name, 'result': 'pass', 'action': 'none',
                'intent_relevance': relevance}

    failure_type, detail = classify_failure(stderr, stdout)
    record: dict = {
        'ts': now,
        'test': test_path.name,
        'failure_type': failure_type,
        'detail': detail,
        'result': 'fail',
        'action': 'none',
        # intent context — WHY this module exists and HOW relevant it is NOW
        'intent_relevance': relevance,
        'last_edit_why': mod_intent.get('edit_why', ''),
        'last_intent_text': mod_intent.get('intent_text', '')[:100],
        'current_intent': intent_ctx.get('intent_text', '')[:80],
    }

    if failure_type == 'import_error':
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

    elif failure_type in ('assertion_error', 'logic_error'):
        # Queue for Gemini upgrade with full intent context attached
        record['action'] = 'queued_for_upgrade'
        record['upgrade_hint'] = (
            f"Last edit: {mod_intent.get('edit_why', 'unknown')}. "
            f"Operator intent: {intent_ctx.get('intent_text', 'unknown')[:80]}. "
            f"Deleted words: {intent_ctx.get('deleted_words', [])[:3]}"
        )

    return record


# ── batch runner ──────────────────────────────────────────────────────────────

def debug_batch(max_modules: int = MAX_MODULES_PER_RUN) -> dict:
    """Debug a batch of failing tests. Intent-aware prioritization.

    Priority order:
      1. import_error AND high intent relevance (hot + broken → fix now)
      2. import_error AND low relevance (cheap to fix regardless)
      3. assertion/logic AND high intent relevance (operator is working here)
      4. assertion/logic AND low relevance (background)
    """
    if not INTERLINK_TESTS.exists():
        return {'fixed': 0, 'still_failing': 0, 'skipped': 0}

    current_intent = _current_intent()
    all_tests = sorted(INTERLINK_TESTS.glob('test_*.py'))

    # quick pre-screen — only process tests that are currently failing
    failing = []
    for t in all_tests:
        passed, _, _ = _run_test(t)
        if not passed:
            failing.append(t)
        if len(failing) >= max_modules * 3:
            break

    # score each test: (is_import_error, -intent_relevance)
    def priority(t: Path) -> tuple:
        _, stdout, stderr = _run_test(t)
        ft, _ = classify_failure(stderr, stdout)
        base = t.stem.removeprefix('test_')
        relevance = _intent_score(base, current_intent)
        is_import = 0 if ft == 'import_error' else 1
        return (is_import, -relevance)

    failing.sort(key=priority)
    to_process = failing[:max_modules]

    fixed = 0
    still_failing = 0
    records = []
    for t in to_process:
        rec = debug_one(t, intent_ctx=current_intent)
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
        'active_intent': current_intent.get('intent_text', '')[:80],
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
