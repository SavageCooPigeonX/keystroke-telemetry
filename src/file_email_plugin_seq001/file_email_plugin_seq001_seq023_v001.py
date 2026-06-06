"""file_email_plugin_seq001_seq023_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from typing import Any
import os
import re

def _learning_closing_scene(wake_order: list[dict[str, Any]], packets: list[dict[str, Any]]) -> str:
    if not wake_order:
        return "No one woke up. That is not mysterious. That is the selector asking to be fixed in public."
    top = Path(str(wake_order[0].get("file") or "top file")).name
    packet_count = len(packets)
    return (
        f"`{top}` is standing at the front with {packet_count} packet(s) behind it, "
        "trying to look brave. The grader is smiling like a locked door. Perfect. That is the shape."
    )


def _all_checks(record: dict[str, Any]) -> list[dict[str, Any]]:
    ten_q = record.get("ten_q") if isinstance(record.get("ten_q"), dict) else {}
    checks = ten_q.get("checks") if isinstance(ten_q.get("checks"), list) else []
    return [item for item in checks if isinstance(item, dict)]


def _failed_checks(record: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in _all_checks(record) if not item.get("passed")]


def _passed_checks(record: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in _all_checks(record) if item.get("passed")]


def _format_check_line(item: dict[str, Any], label: str | None = None) -> str:
    status = label or ("PASS" if item.get("passed") else "FAIL")
    return f"- `{status}` `{item.get('key', 'unknown')}` - {item.get('reason', 'no reason attached')}"


def _actionable_mail_opening(
    file_path: str,
    record: dict[str, Any],
    operator: dict[str, Any],
    memory: dict[str, Any],
    failed_checks: list[dict[str, Any]],
) -> str:
    file_name = Path(file_path).name
    current = operator.get("current_work") or "make file mail actionable"
    if failed_checks:
        return (
            f"Okay, real note from `{file_name}`: I learned the goal, I found the snag, "
            "and I am not going to bury it in polite dashboard soup."
        )
    if memory.get("message_count", 0) > 1:
        return (
            f"Okay, real note from `{file_name}`: this thread has memory now. "
            f"I am using it to help with `{current}` instead of sending decorative status confetti."
        )
    return (
        f"Okay, real note from `{file_name}`: I am making this actionable. "
        f"The live job is `{current}`, and this email is the working memory crumb."
    )
