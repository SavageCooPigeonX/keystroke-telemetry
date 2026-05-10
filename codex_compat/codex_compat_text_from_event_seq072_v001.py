"""codex_compat_text_from_event_seq072_v001.py — Auto-extracted by Pigeon Compiler."""
from typing import Any
import re

def _text_from_event(event: dict[str, Any]) -> str:
    for key in ("content", "text", "message", "prompt", "response"):
        value = event.get(key)
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            parts = []
            for item in value:
                if isinstance(item, dict):
                    parts.append(str(item.get("text") or item.get("content") or ""))
                else:
                    parts.append(str(item))
            return "\n".join(part for part in parts if part)
    return ""
