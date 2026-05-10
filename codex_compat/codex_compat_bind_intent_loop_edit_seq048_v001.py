"""codex_compat_bind_intent_loop_edit_seq048_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_ensure_repo_on_path_seq009_v001 import _ensure_repo_on_path
from pathlib import Path
from typing import Any
import os
import re

def _bind_intent_loop_edit(root: Path, edit_entry: dict[str, Any]) -> dict[str, Any]:
    try:
        _ensure_repo_on_path(root)
        from src.intent_loop_closer_seq001_v001 import bind_edit_to_latest_loop
        return bind_edit_to_latest_loop(root, edit_entry)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
