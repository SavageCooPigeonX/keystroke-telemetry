"""streaming_layer_dataclasses_seq006_v001.py — Pigeon-extracted by compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 13 lines | ~93 tokens
# DESC:   pigeon_extracted_by_compiler
# INTENT: (none)
# LAST:   2026-03-15 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from dataclasses import dataclass, field, asdict
import time

@dataclass
class Alert:
    alert_id: str
    alert_type: str
    severity: str  # "info", "warning", "critical"
    message: str
    timestamp_ms: int
    context: dict = field(default_factory=dict)
    acknowledged: bool = False
