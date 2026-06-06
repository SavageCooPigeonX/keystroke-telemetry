"""file_email_plugin_seq001_seq011_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq012_v001 import _lifecycle_ten_q
from .file_email_plugin_seq001_seq012_v001 import _lifecycle_validation
from .file_email_plugin_seq001_seq013_v001 import _lifecycle_guard
from typing import Any
import os
import re

def _lifecycle_event(loop: dict[str, Any], phase: str) -> dict[str, Any]:
    proposals = loop.get("proposals") if isinstance(loop.get("proposals"), list) else []
    best = proposals[0] if proposals else {}
    ten_q = _lifecycle_ten_q(loop, phase, best)
    guard = _lifecycle_guard(ten_q, phase)
    file_name = "orchestrator/prompt_submission" if phase == "submission" else "orchestrator/intent_completion"
    jobs = [
        str(item.get("deepseek_job_id") or "")
        for item in proposals
        if isinstance(item, dict) and item.get("deepseek_job_id")
    ]
    focus_files = loop.get("focus_files") if isinstance(loop.get("focus_files"), list) else []
    observed_edits = loop.get("observed_edits") if isinstance(loop.get("observed_edits"), list) else []
    return {
        "trigger": phase,
        "event_type": phase,
        "file": file_name,
        "intent_key": loop.get("intent_key", ""),
        "target_state": loop.get("target_state", "interlinked_source_state"),
        "decision": loop.get("status", ""),
        "interlink_score": best.get("interlink_score", 0),
        "beef_with": "operator_approval" if phase == "submission" else "validation_gate",
        "reason": _lifecycle_reason(loop, phase),
        "deepseek_completion_job_id": jobs[0] if jobs else "",
        "context_injection": focus_files[:10],
        "validation_plan": _lifecycle_validation(loop, phase, observed_edits),
        "ten_q": ten_q,
        "orchestrator_email_guard": guard,
    }


def _lifecycle_reason(loop: dict[str, Any], phase: str) -> str:
    prompt = str(loop.get("prompt") or "")[:220]
    if phase == "completion":
        note = str(loop.get("completion_note") or "completion recorded")
        return f"intent loop completed: {note}; prompt: {prompt}"
    return f"prompt submitted into intent loop; human remains on-loop; prompt: {prompt}"
