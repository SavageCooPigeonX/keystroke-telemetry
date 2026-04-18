"""型p_mo_s001_v002_d0323_读唤任_λP_electron_status_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 11 lines | ~80 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from enum import Enum

class ElectronStatus(str, Enum):
    PENDING = "pending"
    FLOWING = "flowing"
    BLOCKED = "blocked"
    STALLED = "stalled"
    LOOPING = "looping"
    DEAD = "dead"
    COMPLETE = "complete"
