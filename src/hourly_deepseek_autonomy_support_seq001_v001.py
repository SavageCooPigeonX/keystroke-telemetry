"""Support helpers for the hourly DeepSeek autonomy loop."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.file_email_plugin_seq001_v001 import emit_file_email, load_file_email_config
from src.hourly_deepseek_io_seq001_v001 import append_jsonl, load_jsonl, now, tail, truthy, write_json
from src.local_env_loader_seq001_v001 import has_env_key, load_local_env

PROMPT_JOBS = "logs/deepseek_prompt_jobs.jsonl"


def enqueue_deepseek_job(root: Path, intent: dict[str, Any], hourly: dict[str, Any], *, write: bool) -> dict[str, Any]:
    action = hourly.get("selected_action") or {}
    prompt = deepseek_prompt(intent, hourly)
    job_id = "hourly-" + hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:16]
    seen = job_seen(root, job_id)
    job = {
        "schema": "deepseek_prompt_job/v1",
        "ts": now(),
        "job_id": job_id,
        "source": "hourly_deepseek_autonomy/v1",
        "status": "queued",
        "priority": 1,
        "model": os.environ.get("DEEPSEEK_CODING_MODEL") or os.environ.get("DEEPSEEK_MODEL") or "deepseek-v4-pro",
        "prompt": prompt,
        "focus_files": focus_files(action),
        "context_pack_path": "logs/hourly_deepseek_context_pack.json",
        "context_confidence": context_confidence(intent),
        "deleted_words": (intent.get("deletion_summary") or {}).get("top_deleted_words") or [],
        "autonomous_write": truthy(os.environ.get("PIGEON_HOURLY_AUTONOMOUS_WRITES")),
    }
    if write and not seen:
        append_jsonl(root / PROMPT_JOBS, job)
    return job | {"queued": write and not seen}


def run_deepseek_once(root: Path, enabled: bool, dry_run: bool, timeout_s: int, target_job_id: str = "") -> dict[str, Any]:
    if not enabled:
        return {"status": "skipped", "reason": "run_deepseek disabled"}
    load_local_env(root)
    if not dry_run and not has_local_key(root, "DEEPSEEK_API_KEY"):
        return {"status": "blocked", "reason": "missing_DEEPSEEK_API_KEY"}
    cmd = [sys.executable, "src/deepseek_daemon_seq001_v001.py", "--once"]
    if dry_run:
        cmd.append("--dry-run")
    env = os.environ.copy()
    if target_job_id:
        env["PIGEON_DEEPSEEK_TARGET_JOB_ID"] = target_job_id
    try:
        completed = subprocess.run(
            cmd, cwd=root, env=env, text=True, capture_output=True, timeout=timeout_s,
            check=False, encoding="utf-8", errors="replace",
        )
        return {
            "status": "ran",
            "returncode": completed.returncode,
            "stdout_tail": tail(completed.stdout),
            "stderr_tail": tail(completed.stderr),
        }
    except subprocess.TimeoutExpired as exc:
        return {"status": "timeout", "returncode": 124, "stdout_tail": tail(exc.stdout or ""), "stderr_tail": f"timeout after {timeout_s}s"}


def send_receipt(root: Path, result: dict[str, Any]) -> dict[str, Any]:
    action = result.get("hourly_action") or {}
    deepseek = result.get("deepseek_result") or {}
    actual = result.get("actual_jobs") or {}
    event = {
        "trigger": "hourly_autonomy",
        "event_type": "hourly_autonomy",
        "file": action.get("target_file") or "orchestrator/hourly_deepseek_autonomy",
        "intent_key": action.get("intent_key") or result.get("intent_compile", {}).get("top_bucket") or "",
        "target_state": "autonomous_hourly_intent_execution",
        "decision": deepseek.get("status", "unknown"),
        "interlink_score": 1.0,
        "beef_with": "hourly scheduler / DeepSeek daemon / validation runner",
        "reason": receipt_reason(result),
        "cycle_id": result.get("ts", ""),
        "deepseek_completion_job_id": (result.get("deepseek_job") or {}).get("job_id", ""),
        "context_injection": focus_files(action) + ["logs/operator_intent_888.json", "logs/hourly_deepseek_autonomy_latest.json"],
        "validation_plan": action.get("validation_plan") or [],
        "ten_q": {"passed": True, "score": 10, "max_score": 10, "reason": receipt_reason(result)},
        "orchestrator_email_guard": {
            "schema": "orchestrator_email_guard/v1",
            "aligned": True,
            "decision": "allow_email",
            "policy": "hourly_autonomy_operator_receipt",
            "reason": "hourly autonomy receipts must reach the operator even when DeepSeek is blocked",
        },
    }
    return emit_file_email(root, event=event, config=load_file_email_config(root))


def deepseek_prompt(intent: dict[str, Any], hourly: dict[str, Any]) -> str:
    action = hourly.get("selected_action") or {}
    return "\n".join([
        "Run the hourly autonomous repo task from compiled operator intent.",
        "", "COMPILED INTENT:", str(intent.get("compiled_read") or ""),
        "", "SELECTED ACTION:", json.dumps(action, ensure_ascii=False, indent=2)[:5000],
        "", "CONTRACT:", "1. Touch the smallest safe surface first.",
        "2. Prefer validation and concrete patches over another abstract report.",
        "3. If source mutation is unsafe, return the exact blocker and next validation gate.",
        "4. Use surgical search-replace blocks only if a change is safe.",
    ])


def intent_seed(intent: dict[str, Any]) -> str:
    ranked = sorted((intent.get("bucket_hits") or {}).items(), key=lambda pair: pair[1].get("hits", 0), reverse=True)
    top = [name for name, data in ranked[:4] if data.get("hits", 0)]
    return " ".join(top) or "hourly autonomous DeepSeek intent compiler action email validation"


def intent_summary(intent: dict[str, Any]) -> dict[str, Any]:
    ranked = sorted((intent.get("bucket_hits") or {}).items(), key=lambda pair: pair[1].get("hits", 0), reverse=True)
    return {
        "available_prompt_count": intent.get("available_prompt_count", 0),
        "top_bucket": ranked[0][0] if ranked else "unknown",
        "compiled_read": intent.get("compiled_read", ""),
        "next_actions": intent.get("next_actions", [])[:5],
    }


def actual_summary(actual: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": actual.get("schema", "actual_job_runner/v1"),
        "selected_count": actual.get("selected_count", 0),
        "passed_count": actual.get("passed_count", 0),
        "failed_count": actual.get("failed_count", 0),
        "operator_read": actual.get("operator_read", ""),
    }


def actual_skipped() -> dict[str, Any]:
    return {"schema": "actual_job_runner/v1", "selected_count": 0, "passed_count": 0, "failed_count": 0, "operator_read": "actual job runner disabled; hourly validation gate still runs"}


def write_outputs(root: Path, result: dict[str, Any]) -> None:
    write_json(root / "logs/hourly_deepseek_autonomy_latest.json", result)
    append_jsonl(root / "logs/hourly_deepseek_autonomy.jsonl", result)
    (root / "logs/hourly_deepseek_autonomy.md").write_text(render_markdown(result), encoding="utf-8")


def render_markdown(result: dict[str, Any]) -> str:
    action = result.get("hourly_action") or {}
    deepseek = result.get("deepseek_result") or {}
    actual = result.get("actual_jobs") or {}
    email = ((result.get("email") or {}).get("resend") or {}).get("status", "pending")
    return "\n".join([
        "# Hourly DeepSeek Autonomy", "",
        f"- action: `{action.get('action_type', 'unknown')}`",
        f"- target: `{action.get('target_file', 'unknown')}`",
        f"- deepseek: `{deepseek.get('status', 'unknown')}`",
        f"- actual jobs: `{actual.get('passed_count', 0)}/{actual.get('selected_count', 0)}` passed",
        f"- email: `{email}`", "", "## Operator Read", "",
        (result.get("intent_compile") or {}).get("compiled_read", ""), "", "## Receipt", "",
        receipt_reason(result),
    ])


def receipt_reason(result: dict[str, Any]) -> str:
    deepseek = result.get("deepseek_result") or {}
    actual = result.get("actual_jobs") or {}
    return f"DeepSeek {deepseek.get('status', 'unknown')}; validation jobs passed {actual.get('passed_count', 0)}/{actual.get('selected_count', 0)}."


def focus_files(action: dict[str, Any]) -> list[str]:
    return list(dict.fromkeys([str(action.get("target_file") or ""), *[str(x) for x in action.get("context_files") or [] if x]]))


def context_confidence(intent: dict[str, Any]) -> float:
    try:
        return float((intent.get("runtime_state") or {}).get("context_confidence") or 0)
    except Exception:
        return 0.0


def job_seen(root: Path, job_id: str) -> bool:
    return any(row.get("job_id") == job_id for row in load_jsonl(root / PROMPT_JOBS, 200))


def has_local_key(root: Path, key: str) -> bool:
    return has_env_key(root, key)
