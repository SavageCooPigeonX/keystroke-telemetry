"""型p_mo_s001_v002_d0323_读唤任_λP_death_cause_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 9 lines | ~72 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from enum import Enum

class DeathCause(str, Enum):
    EXCEPTION = "exception"
    TIMEOUT = "timeout"
    LOOP = "loop"
    MAX_ATTEMPTS = "max_attempts"
    STALE_IMPORT = "stale_import"
