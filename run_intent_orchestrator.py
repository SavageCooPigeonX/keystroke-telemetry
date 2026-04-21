"""run_intent_orchestrator.py — dry-run harness + self-test.

Usage:
  py run_intent_orchestrator.py                  # dry-run pending jobs
  py run_intent_orchestrator.py --selftest       # run built-in dry test
  py run_intent_orchestrator.py --apply          # ACTUALLY commit rewrites (danger)
  py run_intent_orchestrator.py --intent "..." --file file_sim --function self_score
"""
from __future__ import annotations

import sys
import os
import json
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# Import orchestrator
import importlib.util
_spec = importlib.util.spec_from_file_location(
    'intent_orchestrator',
    str(ROOT / 'src' / 'intent_orchestrator_seq001_v001.py'))
_orch = importlib.util.module_from_spec(_spec)
sys.modules['intent_orchestrator'] = _orch  # dataclasses need this
_spec.loader.exec_module(_orch)


def selftest() -> int:
    """End-to-end dry-run of the orchestrator loop with DryRunClient only.
    Proves the state machine wiring works without touching APIs or files.
    """
    print('=' * 60)
    print('SELFTEST: intent_orchestrator (dry-run, DryRunClient only)')
    print('=' * 60)

    # 1. Construct a synthetic IntentJob targeting a known-safe helper
    job = _orch.IntentJob(
        intent_text='simplify self_score gate to use fewer components',
        target_file='file_sim',
        target_function='self_score',
        reason='selftest',
        intent_code='RF',
    )

    # 2. Run with a single DryRunClient so we don't spend credits
    models = [_orch.DryRunClient()]
    result = _orch.orchestrate_job(job, models=models, max_rounds=3, dry_run=True)

    print('\n--- RESULT ---')
    print(json.dumps({k: v for k, v in result.items() if k != 'best_attempt'},
                     indent=2, default=str))

    status = result.get('status')
    if status not in ('accepted', 'escalated'):
        print(f'\nFAIL: unexpected status {status!r}')
        return 1

    # 3. Verify artifacts exist
    logs_dir = ROOT / 'logs'
    orch_log = logs_dir / 'orchestration_log.jsonl'
    attempts_dir = logs_dir / 'rewrite_attempts'
    if not orch_log.exists():
        print('FAIL: orchestration_log.jsonl not written')
        return 1
    if not attempts_dir.exists() or not any(attempts_dir.iterdir()):
        print('FAIL: no candidate attempts written')
        return 1

    print(f'\nPASS: status={status} rounds={result.get("rounds")}')
    print(f'  log:       {orch_log}')
    print(f'  attempts:  {attempts_dir} ({len(list(attempts_dir.iterdir()))} files)')
    return 0


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--selftest', action='store_true')
    p.add_argument('--apply', action='store_true',
                   help='DANGER: actually commit rewrites (default: dry-run)')
    p.add_argument('--max-jobs', type=int, default=3)
    p.add_argument('--max-rounds', type=int, default=_orch.MAX_ROUNDS)
    p.add_argument('--intent', type=str, default=None)
    p.add_argument('--file', type=str, default=None)
    p.add_argument('--function', type=str, default=None)
    args = p.parse_args()

    if args.selftest:
        return selftest()

    if args.intent and args.file:
        job = _orch.IntentJob(intent_text=args.intent, target_file=args.file,
                              target_function=args.function, reason='cli')
        res = _orch.orchestrate_job(job, max_rounds=args.max_rounds,
                                    dry_run=not args.apply)
        print(json.dumps({k: v for k, v in res.items() if k != 'best_attempt'},
                         indent=2, default=str))
        return 0 if res.get('status') == 'accepted' else 1

    results = _orch.run_pending(dry_run=not args.apply, max_jobs=args.max_jobs)
    if not results:
        return 0
    for r in results:
        print(json.dumps({k: v for k, v in r.items() if k != 'best_attempt'},
                         indent=2, default=str))
    accepted = sum(1 for r in results if r.get('status') == 'accepted')
    print(f'\n{accepted}/{len(results)} jobs accepted ({"DRY-RUN" if not args.apply else "APPLIED"})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
