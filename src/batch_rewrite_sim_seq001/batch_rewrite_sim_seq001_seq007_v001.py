"""batch_rewrite_sim_seq001_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from typing import Any
import os
import re

def _job_role(
    index: int,
    rel: str,
    proposal: dict[str, Any],
    failed: list[dict[str, Any]],
    friendships: list[str],
) -> str:
    if index == 0:
        return "captain"
    if failed:
        return "complainant"
    if Path(rel).name.startswith("test_") or any("pytest" in str(step) for step in proposal.get("validation_plan") or []):
        return "validator"
    if friendships:
        return "context_witness"
    return "worker"


def _member_mood(rel: str, failed: list[dict[str, Any]], friendships: list[str], beefs: list[str]) -> str:
    if failed:
        keys = ", ".join(str(item.get("key", "unknown")) for item in failed[:3])
        return f"{Path(rel).name} is loudly pointing at failed checks: {keys}"
    if beefs:
        return f"{Path(rel).name} will cooperate after {Path(beefs[0]).name} stops moving the furniture"
    if friendships:
        return f"{Path(rel).name} wants {Path(friendships[0]).name} loaded beside it before anyone gets clever"
    return f"{Path(rel).name} is calm, which the council considers suspicious"


def _model_grievance(proposal: dict[str, Any], failed: list[dict[str, Any]]) -> str:
    guard = proposal.get("orchestrator_email_guard") or {}
    ten_q = proposal.get("ten_q") or {}
    job_id = str(proposal.get("deepseek_completion_job_id") or "")
    if failed:
        return f"grader blocked the parade: {ten_q.get('reason', 'failed consensus')}"
    if job_id.startswith("blocked"):
        return f"deep path is sulking in `{job_id}` until consensus stops wobbling"
    if not job_id:
        return "deep path has not received a ticket yet"
    if guard.get("decision") != "allow_email":
        return f"email guard said `{guard.get('decision', 'unknown')}` and everyone is pretending that is normal"
    return "model stack behaved, which means validation should still check its pockets"
