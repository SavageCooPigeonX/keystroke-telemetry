"""codex_compat_state_from_deletions_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v002 | 11 lines | ~105 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
import re

def _state_from_deletions(deletion_ratio: float, hesitation_count: int = 0) -> str:
    if deletion_ratio > 0.4 or hesitation_count > 5:
        return "frustrated"
    if deletion_ratio > 0.2 or hesitation_count > 2:
        return "hesitant"
    if deletion_ratio > 0:
        return "neutral"
    return "unknown"
