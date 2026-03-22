"""compliance_seq008_classify_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v004 | 20 lines | ~160 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: stage_78_hook
# LAST:   2026-03-22 @ 276af14
# SESSIONS: 3
# ──────────────────────────────────────────────
import re
from .compliance_seq008_constants_seq001_v001 import MAX_LINES, WARN_LINES, CRIT_LINES

def _classify(lc: int) -> str:
    if lc <= MAX_LINES:
        return 'OK'
    if lc <= WARN_LINES:
        return 'OVER'
    if lc <= CRIT_LINES:
        return 'WARN'
    return 'CRITICAL'
