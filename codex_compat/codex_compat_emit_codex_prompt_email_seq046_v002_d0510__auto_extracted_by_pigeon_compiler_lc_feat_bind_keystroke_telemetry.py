"""codex_compat_emit_codex_prompt_email_seq046_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 046 | VER: v002 | 17 lines | ~187 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from .codex_compat_ensure_repo_on_path_seq009_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _ensure_repo_on_path
from pathlib import Path
from typing import Any
import re

def _emit_codex_prompt_email(
    root: Path,
    prompt_entry: dict[str, Any],
    loop: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        _ensure_repo_on_path(root)
        from src.file_email_plugin_seq001_v001 import emit_codex_prompt_email
        return emit_codex_prompt_email(root, prompt_entry, loop=loop)
    except Exception as exc:
        return {"status": "error", "phase": "codex_prompt", "error": str(exc)}
