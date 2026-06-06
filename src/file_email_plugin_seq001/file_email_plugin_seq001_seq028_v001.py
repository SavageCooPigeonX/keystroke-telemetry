"""file_email_plugin_seq001_seq028_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from typing import Any
import os
import re

def _plain_snip(value: Any, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = re.sub(
        r"\b(?:i am|i'm|they(?:'re|re)|it(?:'s|s))?\s*not the problem\b",
        "[old defensive file-voice phrase]",
        text,
        flags=re.I,
    )
    if len(text) > limit:
        text = text[: max(0, limit - 3)].rstrip() + "..."
    return text


def _old_friend_opening(
    file_path: str,
    record: dict[str, Any],
    operator: dict[str, Any],
    failed_checks: list[dict[str, Any]],
) -> str:
    name = operator.get("operator_name") or "Nikita"
    work = operator.get("current_work") or "make the intent loop sharper than the toolchain around it"
    file_name = Path(file_path).name
    if failed_checks:
        return (
            f"Quick note from `{file_name}`: you were right to be annoyed, {name}. "
            f"The loop is doing useful work, but it is still hiding broken edges unless I drag them into the light."
        )
    if record.get("event_type") == "completion":
        return (
            f"Quick note from `{file_name}`: the loop closed, and I am writing like an old friend "
            f"because the point is your work, not my little file monologue."
        )
    return (
        f"Quick note from `{file_name}`: I saw the move. You are trying to {work}, "
        "so I brought the useful context first and saved the theatrics for after the map."
    )
