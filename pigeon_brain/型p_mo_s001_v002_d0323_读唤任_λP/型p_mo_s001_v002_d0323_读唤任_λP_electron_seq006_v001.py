"""型p_mo_s001_v002_d0323_读唤任_λP_electron_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 17 lines | ~165 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from dataclasses import dataclass, field

@dataclass
class Electron:
    """A tracked unit of intent flowing through the graph — like MessageDraft."""
    job_id: str = ""
    status: str = "pending"
    birth_ms: int = 0
    last_event_ms: int = 0
    path: list = field(default_factory=list)       # files visited in order
    events: list = field(default_factory=list)      # all events
    death_cause: str = ""
    total_calls: int = 0
    total_errors: int = 0
    loop_count: int = 0
    latency_score: float = 0.0                      # like hesitation_score
