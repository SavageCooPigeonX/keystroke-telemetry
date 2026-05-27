"""Closed hourly DeepSeek autonomy loop."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.actual_job_runner_seq001_v001 import run_actual_jobs
from src.hourly_autonomous_file_sim_seq001_v001 import run_hourly_autonomous_file_sim
from src.hourly_deepseek_autonomy_support_seq001_v001 import (
    actual_skipped,
    actual_summary,
    enqueue_deepseek_job,
    intent_seed,
    intent_summary,
    run_deepseek_once,
    send_receipt,
    write_outputs,
)
from src.hourly_deepseek_io_seq001_v001 import now
from src.operator_intent_compiler_seq001_v001 import compile_operator_intent

SCHEMA = "hourly_deepseek_autonomy/v1"


def run_hourly_deepseek_autonomy(
    root: Path,
    *,
    prompt_limit: int = 888,
    limit: int = 8,
    write: bool = True,
    run_validation: bool = True,
    run_actual_jobs_gate: bool = False,
    run_deepseek: bool = True,
    dry_run_deepseek: bool = False,
    timeout_s: int = 160,
) -> dict[str, Any]:
    """Compile intent, run one hourly action, call DeepSeek, validate, email."""
    root = Path(root)
    intent = compile_operator_intent(root, prompt_limit=prompt_limit, write=write)
    hourly = run_hourly_autonomous_file_sim(
        root,
        intent_seed(intent),
        limit=limit,
        write=write,
        run_validation=run_validation,
    )
    job = enqueue_deepseek_job(root, intent, hourly, write=write)
    deepseek = run_deepseek_once(root, run_deepseek, dry_run_deepseek, timeout_s, target_job_id=job.get("job_id", ""))
    actual = (
        run_actual_jobs(root, limit=3, write=write, timeout_s=timeout_s)
        if run_actual_jobs_gate
        else actual_skipped()
    )
    result = {
        "schema": SCHEMA,
        "ts": now(),
        "root": str(root),
        "intent_compile": intent_summary(intent),
        "hourly_action": hourly.get("selected_action", {}),
        "deepseek_job": job,
        "deepseek_result": deepseek,
        "actual_jobs": actual_summary(actual),
        "email": {},
        "paths": {
            "latest": "logs/hourly_deepseek_autonomy_latest.json",
            "history": "logs/hourly_deepseek_autonomy.jsonl",
            "markdown": "logs/hourly_deepseek_autonomy.md",
            "deepseek_jobs": "logs/deepseek_prompt_jobs.jsonl",
        },
    }
    if write:
        write_outputs(root, result)
        result["email"] = send_receipt(root, result)
        write_outputs(root, result)
    return result


def _main() -> int:
    parser = argparse.ArgumentParser(description="Run one hourly DeepSeek autonomy cycle.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--prompt-limit", type=int, default=888)
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--no-validation", action="store_true")
    parser.add_argument("--actual-jobs", action="store_true")
    parser.add_argument("--no-deepseek", action="store_true")
    parser.add_argument("--dry-run-deepseek", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--timeout-s", type=int, default=160)
    args = parser.parse_args()
    result = run_hourly_deepseek_autonomy(
        Path(args.root),
        prompt_limit=args.prompt_limit,
        limit=args.limit,
        write=not args.no_write,
        run_validation=not args.no_validation,
        run_actual_jobs_gate=args.actual_jobs,
        run_deepseek=not args.no_deepseek,
        dry_run_deepseek=args.dry_run_deepseek,
        timeout_s=args.timeout_s,
    )
    print(json.dumps({
        "schema": result["schema"],
        "deepseek": result["deepseek_result"],
        "email": (result.get("email") or {}).get("resend", {}),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())


__all__ = ["run_hourly_deepseek_autonomy"]
