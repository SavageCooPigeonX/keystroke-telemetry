"""codex_compat_bind_intent_loop_response_seq047_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 047 | VER: v002 | 14 lines | ~172 tokens
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

def _bind_intent_loop_response(root: Path, response_entry: dict[str, Any]) -> dict[str, Any]:
    try:
        _ensure_repo_on_path(root)
        from src.intent_loop_closer_seq001_v001 import bind_response_to_latest_loop
        return bind_response_to_latest_loop(root, response_entry)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
