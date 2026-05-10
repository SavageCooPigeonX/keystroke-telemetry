"""codex_compat_close_intent_loop_seq049_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_ensure_repo_on_path_seq009_v001 import _ensure_repo_on_path
from pathlib import Path
from typing import Any
import os
import re

def close_intent_loop(
    root: Path,
    loop_id: str | None = None,
    status: str = "verified",
    note: str = "",
) -> dict[str, Any]:
    try:
        _ensure_repo_on_path(root)
        from src.intent_loop_closer_seq001_v001 import close_intent_loop as _close
        return _close(root, loop_id=loop_id, status=status, note=note)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
