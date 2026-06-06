"""batch_rewrite_sim_seq001_seq021_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq022_v001 import _deepseek_completion_job
from .batch_rewrite_sim_seq001_seq023_v001 import _deepseek_model
from .batch_rewrite_sim_seq001_seq034_v001 import _append_jsonl
from .batch_rewrite_sim_seq001_seq034_v001 import _load_jsonl
from .batch_rewrite_sim_seq001_seq034_v001 import _write_json
from pathlib import Path
from typing import Any
import json
import os
import re

def _render_incompatibilities(proposal: dict[str, Any]) -> str:
    reports = proposal.get("incompatibilities") or []
    if not reports:
        return "none"
    return "; ".join(
        f"{item.get('severity')} with {item.get('with')}: {item.get('reason')}"
        for item in reports[:3]
    )


def _render_ten_q(proposal: dict[str, Any]) -> str:
    ten_q = proposal.get("ten_q") or {}
    status = "PASS" if ten_q.get("passed") else "FAIL"
    return f"{status} {ten_q.get('score', 0)}/{ten_q.get('max_score', 10)} - {ten_q.get('reason', '')}"


def _render_email_guard(proposal: dict[str, Any]) -> str:
    guard = proposal.get("orchestrator_email_guard") or {}
    return f"{guard.get('decision', 'unknown')} - {guard.get('reason', '')}"


def _queue_deepseek_completion_jobs(root: Path, result: dict[str, Any]) -> dict[str, Any]:
    logs = root / "logs"
    jobs = []
    existing = {row.get("job_id") for row in _load_jsonl(logs / "deepseek_code_completion_jobs.jsonl", 200)}
    for proposal in result.get("proposals") or []:
        if proposal.get("overwrite_path") != "eligible_for_deepseek_after_approval":
            continue
        if not ((proposal.get("ten_q") or {}).get("passed") and (proposal.get("orchestrator_email_guard") or {}).get("aligned")):
            proposal["deepseek_completion_job_id"] = "blocked_by_consensus"
            continue
        job = _deepseek_completion_job(result, proposal)
        proposal["deepseek_completion_job_id"] = job["job_id"]
        if job["job_id"] in existing:
            job["duplicate"] = True
            jobs.append(job)
            continue
        _append_jsonl(logs / "deepseek_code_completion_jobs.jsonl", job)
        existing.add(job["job_id"])
        jobs.append(job)
    if jobs:
        _write_json(logs / "deepseek_code_completion_latest.json", jobs[-1])
    return {
        "status": "queued",
        "count": len(jobs),
        "model": _deepseek_model(),
        "jobs": [{"job_id": job["job_id"], "file": job["file"], "status": job["status"]} for job in jobs[:6]],
    }
