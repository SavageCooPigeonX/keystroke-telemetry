"""file_email_plugin_seq001_seq050_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from typing import Any
import os
import re

def _touch_beef(file_path: str, prompt: str) -> str:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_]+", str(prompt).lower())
    if "context" in words:
        return "context_selection"
    if "intent" in words:
        return "intent_key_latest"
    if "test" in words:
        return "the test suite"
    parent = Path(file_path or "").parent.as_posix()
    return parent or "the repo root"


def _subject(file_path: str, beef_with: str, event: dict[str, Any]) -> str:
    stem = Path(file_path).stem or "unknown file"
    enemy = (Path(beef_with).stem or str(beef_with)).strip()
    if event.get("event_type") == "compile":
        return f"group text: {stem} needs {enemy}"
    if event.get("event_type") == "submission":
        verb = "sent an old-friend note about"
    elif event.get("event_type") == "completion":
        verb = "closed the loop and briefed"
    elif event.get("event_type") == "codex_prompt":
        verb = "received a Codex prompt for"
    elif event.get("event_type") == "file_opinion":
        verb = "has an opinion about"
    else:
        verb = "was touched and updated"
    return f"{stem} {verb} {enemy}"


def _event_voice(event_type: Any) -> str:
    if event_type == "compile":
        return "compiled"
    if event_type == "submission":
        return "submitted"
    if event_type == "completion":
        return "completed"
    if event_type == "codex_prompt":
        return "received"
    if event_type == "file_opinion":
        return "opined"
    return "touched"
