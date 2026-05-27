"""File-local coding delegate queue."""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "file_deepseek_delegate/v1"
JOB_LOG = "logs/deepseek_prompt_jobs.jsonl"
LATEST = "logs/file_deepseek_delegate_latest.json"
HISTORY = "logs/file_deepseek_delegate.jsonl"
ARTIFACT_DIR = "logs/file_deepseek_delegate"

def queue_file_deepseek_delegates(
    root: Path,
    packets: list[dict[str, Any]],
    *,
    intent: dict[str, Any] | None = None,
    write: bool = True,
    limit: int = 4,
    model_policy: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Pair file packets with bounded coding delegate jobs."""
    root = Path(root)
    policy = _policy(model_policy)
    selected = [packet for packet in packets if packet.get("file")][: max(1, int(limit or 4))]
    jobs = [_job_for_packet(packet, intent or {}, policy) for packet in selected]
    result = {
        "schema": SCHEMA,
        "ts": _now(),
        "intent_key": (intent or {}).get("intent_key", ""),
        "orchestrator_model": policy["orchestrator_model"],
        "coding_model": policy["coding_model"],
        "file_reasoning_model": policy["file_reasoning_model"],
        "pairing": {
            "orchestrator": "Claude Opus owns repo state, sims, file voices, and apply grading",
            "file_pair": "Gemini reasons about the file while DeepSeek writes patch plus test artifacts",
            "grader": "Claude Opus checks scope, tests, memory, and multi-file coherence before apply",
        },
        "jobs": jobs,
        "grader_contract": _grader_contract(jobs),
        "paths": {"latest": LATEST, "history": HISTORY, "job_log": JOB_LOG, "artifact_dir": ARTIFACT_DIR},
    }
    if write:
        for job in jobs:
            _write_artifact(root, job)
            _append_jsonl(root / JOB_LOG, _deepseek_prompt_job(job))
        _write_json(root / LATEST, result)
        _append_jsonl(root / HISTORY, result)
    return result

def grade_file_delegate_result(
    job: dict[str, Any],
    *,
    changed_files: list[str],
    validations: list[dict[str, Any]],
    tests_written: list[str] | None = None,
) -> dict[str, Any]:
    allowed = set(job.get("allowed_files") or [])
    changed = [str(path) for path in changed_files]
    passed = [row for row in validations if row.get("passed")]
    failed = [row for row in validations if not row.get("passed")]
    out_of_scope = [path for path in changed if path not in allowed]
    required_tests = set(job.get("expected_test_files") or [])
    written_tests = set(tests_written or [])
    accepted = not out_of_scope and not failed and bool(passed) and required_tests.issubset(written_tests | allowed)
    return {
        "schema": "file_deepseek_delegate_grade/v1",
        "ts": _now(),
        "job_id": job.get("job_id", ""),
        "accepted": accepted,
        "decision": "eligible_to_apply" if accepted else "keep_as_artifact",
        "out_of_scope": out_of_scope,
        "passed_validations": [row.get("command", "") for row in passed],
        "failed_validations": [row.get("command", "") for row in failed],
        "backward_learning": {
            "on_accept": "strengthen file-goal, test, and neighbor edges",
            "on_reject": "record missing context, scope leak, or failed gate for earlier wakeup",
        },
    }

def _job_for_packet(packet: dict[str, Any], intent: dict[str, Any], policy: dict[str, str]) -> dict[str, Any]:
    target = str(packet.get("file") or "")
    readiness = ((packet.get("mutation_scope") or {}).get("readiness") or packet.get("readiness") or "")
    tests = _expected_tests(packet, target)
    mode = "patch_and_test" if readiness == "draft_ready" and tests else "explore_and_test_plan"
    tier = 2 if mode == "patch_and_test" else 1
    job_id = "fdd-" + hashlib.sha1(f"{target}|{intent.get('intent_key','')}|{mode}".encode("utf-8")).hexdigest()[:16]
    allowed = _dedupe([target, *tests, *packet.get("required_context", [])])
    return {
        "schema": SCHEMA,
        "job_id": job_id,
        "status": "queued",
        "source": "file_deepseek_delegate/v1",
        "mode": mode,
        "autonomy_tier": tier,
        "model": policy["coding_model"],
        "orchestrator_model": policy["orchestrator_model"],
        "file_reasoning_model": policy["file_reasoning_model"],
        "target_file": target,
        "expected_test_files": tests,
        "allowed_files": allowed,
        "avoid_files": ["secrets", ".env", "unrelated generated logs"],
        "validation_plan": packet.get("validates_with") or [f"py -m py_compile {target}", "git diff --check"],
        "artifact_path": f"{ARTIFACT_DIR}/{job_id}.md",
        "context_files": _dedupe(packet.get("required_context", [])[:10]),
        "prompt": _prompt(packet, intent, mode, tests),
    }

def _prompt(packet: dict[str, Any], intent: dict[str, Any], mode: str, tests: list[str]) -> str:
    target = packet.get("file", "")
    return "\n".join([
        "You are the file-local coding delegate.",
        f"MODE: {mode}",
        f"INTENT_KEY: {intent.get('intent_key', '')}",
        f"TARGET_FILE: {target}",
        f"FILE_GOAL: {', '.join(packet.get('owns') or [])}",
        f"EXPECTED_TESTS: {', '.join(tests) or 'infer minimal test'}",
        "",
        "CONTRACT:",
        "1. Draft a source patch and a matching test together.",
        "2. Keep changes inside allowed files.",
        "3. Include validation commands and expected pass/fail signal.",
        "4. Do not overwrite the repo directly; return an artifact for grader review.",
        "5. State what file memory should learn if the grader accepts or rejects it.",
    ])

def _expected_tests(packet: dict[str, Any], target: str) -> list[str]:
    tests: list[str] = []
    for command in packet.get("validates_with") or []:
        tests.extend(re.findall(r"(test_[\w./\\-]+\.py)", str(command)))
    if not tests and target.endswith(".py"):
        tests.append("test_" + Path(target).stem.replace("_seq001_v001", "") + ".py")
    return _dedupe(tests)

def _grader_contract(jobs: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "apply_requires": ["all validations pass", "changed files subset allowed_files", "test file included", "memory outcome recorded"],
        "jobs": [{"job_id": job["job_id"], "target_file": job["target_file"], "tier": job["autonomy_tier"]} for job in jobs],
        "max_auto_tier_now": 2,
        "direct_overwrite_allowed": False,
    }

def _deepseek_prompt_job(job: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "deepseek_prompt_job/v1",
        "ts": _now(),
        "job_id": job["job_id"],
        "status": "queued",
        "source": job["source"],
        "mode": job["mode"],
        "model": job["model"],
        "prompt": job["prompt"],
        "focus_files": [{"name": path, "score": 1.0} for path in job["allowed_files"][:8]],
        "context_confidence": 0.72 if job["autonomy_tier"] >= 2 else 0.42,
        "autonomous_write": False,
        "write_artifact": True,
        "artifact_path": job["artifact_path"],
    }

def _policy(policy: dict[str, str] | None) -> dict[str, str]:
    policy = policy or {}
    return {
        "orchestrator_model": policy.get("orchestrator_model") or os.environ.get("FILE_ORCHESTRATOR_MODEL") or "claude-opus-orchestrator",
        "file_reasoning_model": policy.get("file_reasoning_model") or os.environ.get("FILE_REASONING_MODEL") or "gemini-file-reasoner",
        "coding_model": policy.get("coding_model") or os.environ.get("DEEPSEEK_CODING_MODEL") or "deepseek-v4-pro",
    }

def _write_artifact(root: Path, job: dict[str, Any]) -> None:
    path = root / job["artifact_path"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# File Delegate Job\n\n```json\n" + json.dumps(job, indent=2) + "\n```\n", encoding="utf-8")

def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def _append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, sort_keys=True) + "\n")

def _dedupe(items: Any) -> list[str]:
    return list(dict.fromkeys(str(item) for item in items if item))

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
