"""file_self_sim_learning_seq001_seq029_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import re

def _overwrite_readiness(node: dict[str, Any], proposal: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    learned = node.get("learned_enough") or {}
    if not settings.get("overwrite_allowed", False):
        return {
            "state": "learning_only",
            "allowed": False,
            "reason": "overwrite is disabled until operator approval and validation outcome exist",
        }
    if not learned.get("enough_for_self_rewrite"):
        return {"state": "needs_more_memory", "allowed": False, "reason": learned.get("reason", "")}
    if proposal.get("approval_gate") != "operator_required":
        return {"state": "missing_operator_gate", "allowed": False, "reason": "approval gate not explicit"}
    return {"state": "ready_after_approval", "allowed": False, "reason": "approval still required"}


def _learned_enough(
    memory: dict[str, Any],
    profile: dict[str, Any],
    growth: list[dict[str, Any]],
    proposal: dict[str, Any],
    tests: list[str],
) -> dict[str, Any]:
    score = 0
    score += 1 if memory.get("messages", 0) else 0
    score += 1 if profile.get("learning_history") else 0
    score += 1 if growth else 0
    score += 1 if proposal else 0
    score += 1 if tests else 0
    enough = score >= 4 and bool(tests)
    return {
        "score": score,
        "enough_for_self_rewrite": enough,
        "reason": "has memory/history/profile/test evidence" if enough else "learning mode needs more memory or validation",
    }
