"""层w_sl_s007_v003_d0317_读唤任_λΠ_stream_client_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 23 lines | ~191 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
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
