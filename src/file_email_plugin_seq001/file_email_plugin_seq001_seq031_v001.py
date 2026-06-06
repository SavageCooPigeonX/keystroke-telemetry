"""file_email_plugin_seq001_seq031_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from typing import Any
import re

def _inline_quote(value: Any, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text:
        return "`none captured`"
    if len(text) > limit:
        text = text[: max(0, limit - 3)].rstrip() + "..."
    return f"`{text}`"


def _operator_text_quote(value: Any, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = re.sub(
        r"\b(?:i am|i'm|they(?:'re|re)|it(?:'s|s))?\s*not the problem\b",
        "[old defensive file-voice phrase]",
        text,
        flags=re.I,
    )
    return _inline_quote(text, limit)


def _comedy_grievance(
    file_path: str,
    beef: str,
    record: dict[str, Any],
    failed_checks: list[dict[str, Any]],
) -> str:
    event_type = record.get("event_type")
    if failed_checks:
        keys = ", ".join(str(item.get("key", "unknown")) for item in failed_checks[:4])
        return (
            f"`{Path(file_path).name}` is not accepting a victory lap while `{keys}` "
            f"is still on the floor wearing a fake badge. `{Path(beef).name}` has been notified."
        )
    if event_type == "completion":
        return "`intent_completion` found no failed checks, which is annoying because now it has to be gracious."
    if event_type == "submission":
        return "`prompt_submission` opened the docket, sharpened the context pencils, and made approval sit in the front row."
    if event_type == "compile":
        return f"`{Path(file_path).name}` has compiled itself into testimony and is politely threatening the next stale model."
    return f"`{Path(file_path).name}` has your back: operator state first, useful context second, jokes only when they carry signal."
