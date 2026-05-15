"""codex_compat_build_unsaid_reconstruction_seq064_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 064 | VER: v002 | 7 lines | ~80 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
import re

def _build_unsaid_reconstruction(final_text: str, deleted_words: list[str]) -> str:
    if not deleted_words:
        return ""
    return f"{final_text[:120]}... (also considered: {' '.join(deleted_words[:8])})"
