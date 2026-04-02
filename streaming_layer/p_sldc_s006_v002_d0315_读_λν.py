"""streaming_layer_dataclasses_seq006_v001.py — Pigeon-extracted by compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v002 | 21 lines | ~154 tokens
# DESC:   pigeon_extracted_by_compiler
# INTENT: verify_pigeon_plugin
# LAST:   2026-03-15 @ caac48c
# SESSIONS: 1
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
