"""file_email_plugin_seq001_seq038_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq023_v001 import _failed_checks
from .file_email_plugin_seq001_seq040_v001 import _append_unique
from .file_email_plugin_seq001_seq040_v001 import _dedupe_list
from typing import Any
import re

def _apply_mail_memory_commands(knowledge: dict[str, Any], commands: dict[str, list[str]]) -> dict[str, Any]:
    for note in commands.get("remember", []):
        _append_unique(knowledge.setdefault("operator_notes", []), note)
    for item in commands.get("use", []):
        _append_unique(knowledge.setdefault("preferred_context", []), item)
    for item in commands.get("avoid", []):
        _append_unique(knowledge.setdefault("avoid_rules", []), item)
    for item in commands.get("style", []):
        _append_unique(knowledge.setdefault("style_notes", []), item)
    return knowledge


def _parse_mail_memory_commands(message: str) -> dict[str, list[str]]:
    commands = {"remember": [], "use": [], "avoid": [], "style": [], "note": []}
    for raw in str(message or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        match = re.match(r"^(remember|use|avoid|style)\s*:\s*(.+)$", line, re.I)
        if match:
            key = match.group(1).lower()
            values = _split_mail_command_values(match.group(2)) if key == "use" else [match.group(2).strip()]
            commands[key].extend(values)
        else:
            commands["note"].append(line)
    return {key: value for key, value in commands.items() if value}


def _split_mail_command_values(value: str) -> list[str]:
    parts = [part.strip() for part in re.split(r",|\s+\+\s+|\s+;\s+", value) if part.strip()]
    return parts or [value.strip()]


def _file_memory_tags(record: dict[str, Any]) -> list[str]:
    operator = record.get("operator_state") if isinstance(record.get("operator_state"), dict) else {}
    tags = ["file_mail", str(record.get("event_type") or "event")]
    if operator.get("primary_operator_intent"):
        tags.append(str(operator.get("primary_operator_intent")))
    if _failed_checks(record):
        tags.append("failed_checks")
    if record.get("intent_key"):
        tags.append("intent_keyed")
    return _dedupe_list(tags)
