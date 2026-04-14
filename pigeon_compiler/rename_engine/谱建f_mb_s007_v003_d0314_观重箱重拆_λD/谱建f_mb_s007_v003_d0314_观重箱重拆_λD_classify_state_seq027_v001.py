"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_classify_state_seq027_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 027 | VER: v001 | 22 lines | ~180 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def _classify_msg_state(msg: dict) -> str:
    """Lightweight cognitive state classification for summary display."""
    keys = max(msg.get('total_keystrokes', 0), 1)
    dels = msg.get('total_deletions', 0)
    hes = msg.get('hesitation_score', 0.0)
    del_ratio = dels / keys
    if msg.get('deleted'):
        return 'abandoned'
    if hes > 0.6:
        return 'frustrated'
    if hes > 0.4:
        return 'hesitant'
    if del_ratio > 0.20:
        return 'restructuring'
    if hes < 0.15 and del_ratio < 0.05:
        return 'flow'
    if hes < 0.25:
        return 'focused'
    return 'neutral'
