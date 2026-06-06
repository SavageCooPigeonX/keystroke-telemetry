"""file_email_plugin_seq001_seq029_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq031_v001 import _operator_text_quote
from pathlib import Path
from typing import Any
import os
import re

def _old_friend_read(
    file_path: str,
    record: dict[str, Any],
    operator: dict[str, Any],
    failed_checks: list[dict[str, Any]],
) -> str:
    if failed_checks:
        keys = ", ".join(str(item.get("key", "unknown")) for item in failed_checks[:3])
        return f"you are close, but `{keys}` still needs receipts before I let the system call it done"
    intent = operator.get("primary_operator_intent") or "intent routing"
    return (
        f"you are steering `{intent}`; `{Path(file_path).name}` should flatter the mission by being useful, "
        "specific, and impossible to confuse with generic status spam"
    )


def _adaptive_operator_note(
    file_path: str,
    record: dict[str, Any],
    operator: dict[str, Any],
    memory: dict[str, Any],
    failed_checks: list[dict[str, Any]],
) -> str:
    current = operator.get("current_work") or "make file memory follow the way you actually think"
    latest = _operator_text_quote(operator.get("latest_operator_text") or "", 220)
    file_name = Path(file_path).name
    memory_note = ""
    if memory.get("message_count"):
        memory_note = f" This is message {memory.get('message_count')} in this thread, so this is becoming memory, not a one-off alert."
    if failed_checks:
        keys = ", ".join(str(item.get("key", "unknown")) for item in failed_checks[:3])
        return (
            f"I think the live move is this: {current}. `{file_name}` should help by remembering the conversation, "
            f"not by forcing your thought into ten little boxes. The only hard stop I see is `{keys}`.{memory_note}\n\n"
            f"Recent operator signal: {latest}"
        )
    return (
        f"I think the live move is this: {current}. `{file_name}` should adapt to that, keep the thread memory, "
        f"and only expose structure when another tool needs a handle.{memory_note}\n\n"
        f"Recent operator signal: {latest}"
    )
