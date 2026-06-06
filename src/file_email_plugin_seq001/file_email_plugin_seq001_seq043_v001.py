"""file_email_plugin_seq001_seq043_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import re

def _current_work_summary(
    latest_text: str,
    primary: str,
    event: dict[str, Any],
    council_latest: dict[str, Any],
) -> str:
    lower = str(latest_text or "").lower()
    if any(bit in lower for bit in ("actionable", "what its learned", "what it learned", "what got done", "planning", "personalization", "written by chat gpt")):
        return "make visible file mail show what it learned, what got done, what comes next, and what it needs"
    if ("email" in lower or "mail" in lower) and ("memory" in lower or "knowledge" in lower or "messages" in lower):
        return "manage files through email threads and store file knowledge as long-term memory"
    if "manage my files" in lower:
        return "manage files through conversational mail instead of forcing rigid prompt boxes"
    if "old friend" in lower or "sycophantic" in lower:
        return "make file emails read like operator-aware notes from a trusted collaborator"
    if "operatorstate" in lower or ("operator" in lower and "state" in lower):
        return "center file telemetry on the live operator model instead of generic file status"
    if council_latest.get("comedy_summary"):
        return str(council_latest.get("comedy_summary"))
    if primary == "telemetry_email":
        return "turn prompt telemetry into useful local mail and context requests"
    if event.get("intent_key"):
        return f"advance `{event.get('intent_key')}`"
    return "keep the intent loop visible and operator-aligned"


def _state_source(
    semantic_latest: dict[str, Any],
    operator_current: dict[str, Any],
    prompt_latest: dict[str, Any],
) -> str:
    sources = []
    if semantic_latest:
        sources.append("semantic_profile_latest")
    if operator_current:
        sources.append("operator_state_current")
    if prompt_latest:
        sources.append("prompt_journal")
    return "+".join(sources) or "event_only"
