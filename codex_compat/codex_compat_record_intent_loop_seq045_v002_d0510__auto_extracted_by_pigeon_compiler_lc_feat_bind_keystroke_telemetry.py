"""codex_compat_record_intent_loop_seq045_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 045 | VER: v002 | 30 lines | ~274 tokens
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

def _record_intent_loop(
    root: Path,
    prompt: str,
    context_selection: dict[str, Any] | None = None,
    file_sim: dict[str, Any] | None = None,
    prompt_brain: dict[str, Any] | None = None,
    source: str = "prompt",
    deleted_words: list[str] | None = None,
) -> dict[str, Any]:
    try:
        _ensure_repo_on_path(root)
        from src.intent_loop_closer_seq001_v001 import record_intent_loop
        return record_intent_loop(
            root,
            prompt,
            context_selection=context_selection,
            file_sim=file_sim,
            prompt_brain=prompt_brain,
            source=source,
            deleted_words=deleted_words,
        )
    except Exception as exc:
        return {"status": "error", "error": str(exc), "source": source}
