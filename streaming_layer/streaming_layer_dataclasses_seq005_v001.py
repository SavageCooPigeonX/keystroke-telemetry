"""streaming_layer_dataclasses_seq005_v001.py — Pigeon-extracted by compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 23 lines | ~186 tokens
# DESC:   pigeon_extracted_by_compiler
# INTENT: (none)
# LAST:   2026-03-15 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from dataclasses import dataclass, field, asdict
import json
import queue as _queue_mod

@dataclass
class StreamClient:
    client_id: str
    connected_at_ms: int
    format: str = "json"
    queue: _queue_mod.Queue = field(default_factory=lambda: _queue_mod.Queue(maxsize=500))
    filters: dict = field(default_factory=dict)
    active: bool = True
    events_sent: int = 0
    last_heartbeat_ms: int = 0

    def matches_filter(self, event: dict) -> bool:
        if not self.filters:
            return True
        for key, value in self.filters.items():
            if key in event and event[key] != value:
                return False
        return True
