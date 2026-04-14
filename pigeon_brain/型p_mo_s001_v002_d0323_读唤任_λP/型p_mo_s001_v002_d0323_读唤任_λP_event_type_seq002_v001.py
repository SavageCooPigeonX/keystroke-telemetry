"""型p_mo_s001_v002_d0323_读唤任_λP_event_type_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 10 lines | ~67 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from enum import Enum

class EventType(str, Enum):
    START = "start"
    CALL = "call"
    RETURN = "return"
    ERROR = "error"
    TIMEOUT = "timeout"
    LOOP = "loop"
