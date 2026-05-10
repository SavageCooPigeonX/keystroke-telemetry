"""codex_compat_get_intent_loop_status_seq050_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_ensure_repo_on_path_seq009_v001 import _ensure_repo_on_path
from pathlib import Path
from typing import Any
import os
import re

def get_intent_loop_status(root: Path) -> dict[str, Any]:
    try:
        _ensure_repo_on_path(root)
        from src.intent_loop_closer_seq001_v001 import intent_loop_summary
        return intent_loop_summary(root)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
