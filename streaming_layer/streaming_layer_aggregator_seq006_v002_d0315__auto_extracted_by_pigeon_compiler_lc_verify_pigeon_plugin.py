"""streaming_layer_aggregator_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v002 | 97 lines | ~856 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: verify_pigeon_plugin
# LAST:   2026-03-15 @ caac48c
# SESSIONS: 1
# ──────────────────────────────────────────────
from collections import deque
from src.timestamp_utils_seq001_v002_d0315__millisecond_epoch_timestamp_utility_lc_verify_pigeon_plugin import _now_ms
from typing import Optional, Callable
import statistics
import time

class EventAggregator:
    """Sliding-window aggregation of telemetry events."""

    def __init__(self, window_sizes_ms: list[int] = None):
        self.window_sizes = window_sizes_ms or AGGREGATION_INTERVALS
        self._events: deque = deque(maxlen=EVENT_BUFFER_SIZE)
        self._buckets: dict[int, AggregationBucket] = {}
        self._reset_buckets()

    def _reset_buckets(self):
        now = _now_ms()
        for ws in self.window_sizes:
            self._buckets[ws] = AggregationBucket(window_ms=ws, start_ms=now)

    def ingest(self, event: dict):
        self._events.append(event)
        now = _now_ms()

        for ws, bucket in self._buckets.items():
            # rotate bucket if window expired
            if now - bucket.start_ms > ws:
                self._buckets[ws] = AggregationBucket(window_ms=ws, start_ms=now)
                bucket = self._buckets[ws]
            bucket.add_event(event)

    def get_snapshot(self) -> dict:
        return {
            "timestamp_ms": _now_ms(),
            "total_buffered": len(self._events),
            "windows": {
                str(ws): bucket.to_dict()
                for ws, bucket in self._buckets.items()
            },
        }

    def get_window(self, window_ms: int) -> Optional[dict]:
        bucket = self._buckets.get(window_ms)
        if bucket:
            return bucket.to_dict()
        return None

    def recent_events(self, count: int = 20) -> list[dict]:
        items = list(self._events)
        return items[-count:]

    def compute_rolling_wpm(self, window_ms: int = 5000) -> float:
        now = _now_ms()
        cutoff = now - window_ms
        inserts = 0
        earliest = now
        for e in reversed(list(self._events)):
            ts = e.get("timestamp_ms", 0)
            if ts < cutoff:
                break
            if e.get("event_type") == "insert":
                inserts += 1
            if ts < earliest:
                earliest = ts
        elapsed_min = max((now - earliest) / 60_000, 0.01)
        return round((inserts / 5) / elapsed_min, 1)

    def compute_deletion_velocity(self, window_ms: int = 5000) -> dict:
        """How fast the user is deleting — consecutive delete speed."""
        now = _now_ms()
        cutoff = now - window_ms
        delete_deltas = []
        for e in reversed(list(self._events)):
            ts = e.get("timestamp_ms", 0)
            if ts < cutoff:
                break
            if e.get("event_type") in ("delete", "backspace"):
                delete_deltas.append(e.get("delta_ms", 0))

        if not delete_deltas:
            return {"count": 0, "avg_ms": 0, "burst": False}

        avg = statistics.mean(delete_deltas)
        return {
            "count": len(delete_deltas),
            "avg_ms": round(avg, 1),
            "burst": len(delete_deltas) >= 3 and avg < 100,
        }
