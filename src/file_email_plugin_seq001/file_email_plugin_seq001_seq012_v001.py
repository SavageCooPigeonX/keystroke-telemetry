"""file_email_plugin_seq001_seq012_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import os
import re

def _lifecycle_validation(loop: dict[str, Any], phase: str, observed_edits: list[dict[str, Any]]) -> list[str]:
    if phase == "completion":
        files = [str(item.get("file")) for item in observed_edits[:6] if isinstance(item, dict) and item.get("file")]
        checks = ["completion receipt recorded", "training candidate generated"]
        checks.extend(f"review bound edit `{file_name}`" for file_name in files)
        return checks[:8]
    return [
        "prompt receipt recorded",
        "intent loop ticket written",
        "dynamic context pack injected",
        "operator approval required before overwrite",
    ]


def _lifecycle_ten_q(loop: dict[str, Any], phase: str, best: dict[str, Any]) -> dict[str, Any]:
    if isinstance(best.get("ten_q"), dict) and best["ten_q"]:
        return best["ten_q"]
    proposals = loop.get("proposals") if isinstance(loop.get("proposals"), list) else []
    observed_edits = loop.get("observed_edits") if isinstance(loop.get("observed_edits"), list) else []
    closed = str(loop.get("status") or "") in {"verified", "done", "resolved"}
    checks = [
        {"key": "intent_alignment", "passed": bool(loop.get("intent_key")), "reason": "intent loop has an intent key"},
        {"key": "context_available", "passed": bool(loop.get("focus_files")), "reason": "focus files/context selected"},
        {"key": "source_target", "passed": bool(proposals or observed_edits), "reason": "source proposal or bound edit exists"},
        {"key": "validation_plan", "passed": phase == "submission" or closed, "reason": "submission is gated; completion requires verified close"},
        {"key": "operator_approval", "passed": bool(loop.get("approval_required", True)), "reason": "operator approval remains required"},
        {"key": "completion_bound", "passed": phase == "submission" or bool(observed_edits), "reason": "completion has bound edits" if observed_edits else "no bound edits yet"},
        {"key": "training_candidate", "passed": phase == "submission" or bool(observed_edits), "reason": "bound edits can train future routing" if observed_edits else "awaiting execution"},
        {"key": "stale_date_guard", "passed": bool(loop.get("updated_ts") or loop.get("ts")), "reason": "loop timestamp exists"},
        {"key": "human_on_loop", "passed": loop.get("human_position") == "on_loop", "reason": "human is approval/veto, not hidden in-loop"},
        {"key": "no_autowrite", "passed": not bool(loop.get("auto_write_allowed")), "reason": "autonomous overwrite is blocked"},
    ]
    score = sum(1 for item in checks if item["passed"])
    return {
        "schema": "prompt_lifecycle_10q/v1",
        "score": score,
        "max_score": 10,
        "min_score": 7,
        "passed": score >= 7,
        "reason": "passed" if score >= 7 else "prompt lifecycle needs more bound evidence",
        "checks": checks,
    }
