"""streaming_layer_dataclasses_seq006_v001.py — Pigeon-extracted by compiler."""

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
