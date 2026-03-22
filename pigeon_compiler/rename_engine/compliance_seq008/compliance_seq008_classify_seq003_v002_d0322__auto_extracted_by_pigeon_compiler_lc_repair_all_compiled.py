"""compliance_seq008_classify_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v002 | 12 lines | ~93 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: repair_all_compiled
# LAST:   2026-03-22 @ e4f5ad3
# SESSIONS: 1
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
