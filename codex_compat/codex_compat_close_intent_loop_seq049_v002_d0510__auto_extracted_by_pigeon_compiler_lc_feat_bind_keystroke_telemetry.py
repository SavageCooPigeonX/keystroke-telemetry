"""codex_compat_close_intent_loop_seq049_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 049 | VER: v002 | 19 lines | ~183 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from .codex_compat_ensure_repo_on_path_seq009_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _ensure_repo_on_path
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
