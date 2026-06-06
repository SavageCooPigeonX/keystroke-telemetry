"""codex_compat_seq015_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_seq002_v001 import _load_jsonl_tail
from pathlib import Path
from typing import Any
import json
import os
import re

def _surface_activity(root: Path) -> dict[str, Any]:
    logs = root / "logs"
    uia_rows = _load_jsonl_tail(logs / "uia_live.jsonl", max_lines=200)
    key_rows = _load_jsonl_tail(logs / "os_keystrokes.jsonl", max_lines=200)

    latest_switch = None
    for row in reversed(uia_rows):
        if row.get("event") == "context_switch":
            latest_switch = {
                "ts": row.get("ts"),
                "from": row.get("from"),
                "to": row.get("to"),
                "name": row.get("name"),
                "class": row.get("class"),
                "auto_id": row.get("auto_id"),
            }
            break

    latest_key = key_rows[-1] if key_rows else {}
    latest_uia = uia_rows[-1] if uia_rows else {}
    return {
        "latest_context_switch": latest_switch,
        "latest_key_context": latest_key.get("context"),
        "latest_key_surface": latest_key.get("surface"),
        "latest_key_type": latest_key.get("type"),
        "latest_key_buffer_len": latest_key.get("buffer_len"),
        "latest_uia_context": latest_uia.get("context"),
        "latest_uia_event": latest_uia.get("event"),
        "uia_rows_seen": len(uia_rows),
        "keystroke_rows_seen": len(key_rows),
    }
