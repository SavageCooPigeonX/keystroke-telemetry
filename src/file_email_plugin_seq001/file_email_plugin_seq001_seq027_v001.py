"""file_email_plugin_seq001_seq027_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from typing import Any
import re

def _actionable_comedy_line(
    file_path: str,
    beef: str,
    record: dict[str, Any],
    operator: dict[str, Any],
    memory: dict[str, Any],
    failed_checks: list[dict[str, Any]],
) -> str:
    file_name = Path(file_path).name
    if failed_checks:
        return (
            f"`{file_name}` is side-eyeing `{failed_checks[0].get('key', 'unknown')}` so hard the router felt it in JSON."
        )
    if memory.get("message_count", 0) > 2:
        return f"`{file_name}` has a mail thread now and is already acting like it owns a tiny office with strong opinions."
    if beef and beef != "unknown":
        return f"`{file_name}` is cooperating with `{Path(beef).name}`, but only because your intent said so."
    return f"`{file_name}` promises fewer clipboards and more useful notes."


def _memory_knowledge(memory: dict[str, Any]) -> dict[str, Any]:
    knowledge = memory.get("knowledge") if isinstance(memory.get("knowledge"), dict) else {}
    return knowledge


def _preferred_context(record: dict[str, Any], knowledge: dict[str, Any]) -> list[str]:
    context = [str(item) for item in (record.get("context_injection") or []) if item]
    context.extend(str(item) for item in (knowledge.get("preferred_context") or []) if item)
    out = []
    seen = set()
    for item in context:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _first_validation(record: dict[str, Any]) -> str:
    validation = record.get("validation_plan") or []
    if validation:
        return str(validation[0])
    return "ask for context before rewrite"


def _failed_check_summary(failed_checks: list[dict[str, Any]]) -> str:
    return ", ".join(f"{item.get('key', 'unknown')}={item.get('reason', '')}" for item in failed_checks[:4])
