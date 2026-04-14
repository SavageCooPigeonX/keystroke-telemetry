"""型p_mo_s001_v002_d0323_读唤任_λP_execution_event_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 15 lines | ~128 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from dataclasses import dataclass, field

@dataclass
class ExecutionEvent:
    """Single event in an electron's lifecycle — like KeyEvent for agents."""
    schema: str = SCHEMA_VERSION
    timestamp_ms: int = 0
    event_type: str = "call"
    from_file: str = ""
    to_file: str = ""
    job_id: str = ""
    status: str = "in_progress"
    delta_ms: int = 0
    context: dict = field(default_factory=dict)
