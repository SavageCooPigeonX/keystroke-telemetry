"""file_email_plugin_seq001_seq042_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import re

def _latest_operator_text(
    semantic_latest: dict[str, Any],
    prompt_latest: dict[str, Any],
    brain_latest: dict[str, Any],
    event: dict[str, Any],
) -> str:
    for source in (semantic_latest, prompt_latest, brain_latest, event):
        if not isinstance(source, dict):
            continue
        for key in ("text", "msg", "prompt", "final_text", "reason"):
            value = str(source.get(key) or "").strip()
            if value:
                return value
    return ""


def _infer_operator_intent(text: str, semantic_intents: list[str], event: dict[str, Any]) -> str:
    lower = str(text or "").lower()
    if any(bit in lower for bit in ("actionable", "what its learned", "what it learned", "what got done", "planning", "personalization", "written by chat gpt")):
        return "file_voice_design"
    if ("email" in lower or "mail" in lower) and ("memory" in lower or "knowledge" in lower or "messages" in lower):
        return "file_memory_management"
    if "operatorstate" in lower or ("operator" in lower and "state" in lower):
        return "operator_state_modeling"
    if "old friend" in lower or "sycophantic" in lower or ("email" in lower and "feel" in lower):
        return "file_voice_design"
    if "email" in lower or "mail" in lower:
        return "telemetry_email"
    if "reasoning" in lower:
        return "reasoning_depth"
    for intent in semantic_intents:
        if intent and intent != "unknown":
            return intent
    if event.get("event_type") in {"submission", "completion"}:
        return "prompt_lifecycle"
    return "unknown"
