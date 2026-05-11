"""codex_compat_words_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v002 | 5 lines | ~58 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
import re

def _words(text: str) -> list[str]:
    return [part.strip(".,;:!?()[]{}\"'`") for part in str(text).split() if part.strip(".,;:!?()[]{}\"'`")]
