"""batch_rewrite_sim_seq001_seq018_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq019_v001 import _ten_q_checks
from .batch_rewrite_sim_seq001_seq020_v001 import _orchestrator_email_guard
from .batch_rewrite_sim_seq001_seq020_v001 import _ten_q_failure_reason
from typing import Any
import os
import re

def _attach_consensus_scores(
    proposals: list[dict[str, Any]],
    compiled: dict[str, Any],
    config: dict[str, Any],
) -> None:
    guard = config.get("consensus_guard") if isinstance(config.get("consensus_guard"), dict) else {}
    enabled = bool(guard.get("enabled", True))
    for proposal in proposals:
        ten_q = _compute_ten_q(proposal, compiled, guard)
        if not enabled:
            ten_q["passed"] = True
            ten_q["reason"] = "consensus_guard_disabled"
        proposal["ten_q"] = ten_q
        proposal["orchestrator_email_guard"] = _orchestrator_email_guard(proposal, ten_q, guard)


def _compute_ten_q(
    proposal: dict[str, Any],
    compiled: dict[str, Any],
    guard: dict[str, Any],
) -> dict[str, Any]:
    checks = _ten_q_checks(proposal, compiled)
    score = sum(1 for check in checks if check.get("passed"))
    by_key = {str(check.get("key")): bool(check.get("passed")) for check in checks}
    required = [str(item) for item in (guard.get("required_passes") or []) if item]
    min_score = int(guard.get("min_score") or 7)
    missing = [key for key in required if not by_key.get(key)]
    passed = score >= min_score and not missing
    return {
        "schema": "file_consensus_10q/v1",
        "score": score,
        "max_score": len(checks),
        "min_score": min_score,
        "passed": passed,
        "required_passes": required,
        "missing_required": missing,
        "checks": checks,
        "reason": "passed" if passed else _ten_q_failure_reason(score, min_score, missing),
    }
