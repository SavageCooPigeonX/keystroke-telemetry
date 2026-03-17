# @pigeon: seq=007 | role=streaming_layer | depends=[logger,models,context_budget,drift_watcher,resistance_bridge] | exports=[StreamingTelemetryServer,LiveDashboard,EventAggregator,SessionReplay,AlertEngine,MetricsCollector,StreamFormatter,ConnectionPool] | tokens=~12000 | coupling=0.9
"""streaming_layer_seq007_v001.py — MONOLITHIC live streaming interface for keystroke telemetry.

This file is INTENTIONALLY oversized to test the Pigeon Code Compiler.
It contains 8 classes and ~15 functions crammed into a single module.

Features:
  - WebSocket-style event broadcasting to connected clients
  - Server-Sent Events (SSE) endpoint simulation
  - Live dashboard with rolling stats
  - Event aggregation with sliding windows
  - Session replay from JSONL logs
  - Alert engine for anomaly detection
  - Metrics collector with percentile computation
  - Connection pool management
  - Stream formatting (JSON, CSV, compact)
"""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v003 | 1155 lines | ~10,192 tokens
# DESC:   monolithic_live_streaming_interface_for
# INTENT: pulse_telemetry_prompt
# LAST:   2026-03-17 @ 9e2a305
# SESSIONS: 1
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# ── /pulse ──

import json
import time
import uuid
import threading
import queue as _queue_mod
import math
import statistics
import os
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable
from http.server import HTTPServer, BaseHTTPRequestHandler
from collections import deque

from src.timestamp_utils_seq001_v003_d0317__millisecond_epoch_timestamp_utility_lc_pulse_telemetry_prompt import _now_ms
from src.models_seq002_v003_d0317__dataclasses_for_keystroke_events_and_lc_pulse_telemetry_prompt import KeyEvent, MessageDraft
from src.logger_seq003_v003_d0317__core_keystroke_telemetry_logger_lc_pulse_telemetry_prompt import TelemetryLogger, SCHEMA_VERSION
from src.context_budget_seq004_v007_d0317__context_budget_scorer_for_llm_lc_pulse_telemetry_prompt import score_context_budget, estimate_tokens
from src.resistance_bridge_seq006_v003_d0317__bridge_between_keystroke_telemetry_and_lc_pulse_telemetry_prompt import HesitationAnalyzer


# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

DEFAULT_PORT = 8787
MAX_CLIENTS = 50
EVENT_BUFFER_SIZE = 1000
SLIDING_WINDOW_MS = 30_000  # 30 seconds
ALERT_COOLDOWN_MS = 5_000
HEARTBEAT_INTERVAL_MS = 10_000
MAX_REPLAY_EVENTS = 10_000
PERCENTILE_TARGETS = [50, 75, 90, 95, 99]
CSV_SEPARATOR = ","
COMPACT_SEPARATOR = "|"

STREAM_FORMATS = {
    "json": "application/json",
    "csv": "text/csv",
    "compact": "text/plain",
    "sse": "text/event-stream",
}

ALERT_THRESHOLDS = {
    "pause_duration_ms": 5000,
    "deletion_burst_length": 10,
    "wpm_drop_percent": 50,
    "hesitation_score": 0.7,
    "discard_streak": 3,
}

DASHBOARD_REFRESH_MS = 500
AGGREGATION_INTERVALS = [5_000, 15_000, 30_000, 60_000]  # 5s, 15s, 30s, 60s


# ═══════════════════════════════════════════════════════════════════
# DATA CLASSES
# ═══════════════════════════════════════════════════════════════════

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


@dataclass
class AggregationBucket:
    window_ms: int
    start_ms: int
    events: list = field(default_factory=list)
    insert_count: int = 0
    delete_count: int = 0
    paste_count: int = 0
    total_delta_ms: int = 0
    pause_count: int = 0
    max_delta_ms: int = 0
    min_delta_ms: int = 999999
    submit_count: int = 0
    discard_count: int = 0

    def add_event(self, event: dict):
        self.events.append(event)
        etype = event.get("event_type", "")
        delta = event.get("delta_ms", 0)

        if etype == "insert":
            self.insert_count += 1
        elif etype in ("delete", "backspace"):
            self.delete_count += 1
        elif etype == "paste":
            self.paste_count += 1
        elif etype == "submit":
            self.submit_count += 1
        elif etype in ("clear", "discard"):
            self.discard_count += 1

        self.total_delta_ms += delta
        if delta > self.max_delta_ms:
            self.max_delta_ms = delta
        if delta < self.min_delta_ms and delta > 0:
            self.min_delta_ms = delta
        if delta > 2000:
            self.pause_count += 1

    def avg_delta_ms(self) -> float:
        if not self.events:
            return 0.0
        return self.total_delta_ms / len(self.events)

    def estimated_wpm(self) -> float:
        if self.insert_count == 0 or self.total_delta_ms == 0:
            return 0.0
        chars_per_ms = self.insert_count / self.total_delta_ms
        return round(chars_per_ms * 60_000 / 5, 1)  # words = chars / 5

    def deletion_ratio(self) -> float:
        total = self.insert_count + self.delete_count
        if total == 0:
            return 0.0
        return round(self.delete_count / total, 3)

    def to_dict(self) -> dict:
        return {
            "window_ms": self.window_ms,
            "start_ms": self.start_ms,
            "event_count": len(self.events),
            "insert_count": self.insert_count,
            "delete_count": self.delete_count,
            "paste_count": self.paste_count,
            "submit_count": self.submit_count,
            "discard_count": self.discard_count,
            "pause_count": self.pause_count,
            "avg_delta_ms": round(self.avg_delta_ms(), 1),
            "max_delta_ms": self.max_delta_ms,
            "min_delta_ms": self.min_delta_ms if self.min_delta_ms < 999999 else 0,
            "estimated_wpm": self.estimated_wpm(),
            "deletion_ratio": self.deletion_ratio(),
        }


@dataclass
class Alert:
    alert_id: str
    alert_type: str
    severity: str  # "info", "warning", "critical"
    message: str
    timestamp_ms: int
    context: dict = field(default_factory=dict)
    acknowledged: bool = False


# ═══════════════════════════════════════════════════════════════════
# STREAM FORMATTER
# ═══════════════════════════════════════════════════════════════════

class StreamFormatter:
    """Formats telemetry events into different output formats."""

    @staticmethod
    def to_json(event: dict) -> str:
        return json.dumps(event)

    @staticmethod
    def to_json_pretty(event: dict) -> str:
        return json.dumps(event, indent=2)

    @staticmethod
    def to_csv(event: dict, headers: bool = False) -> str:
        keys = ["seq", "timestamp_ms", "delta_ms", "event_type", "key",
                "cursor_pos", "buffer_len", "message_id", "session_id"]
        if headers:
            header_line = CSV_SEPARATOR.join(keys) + "\n"
        else:
            header_line = ""
        values = [str(event.get(k, "")) for k in keys]
        return header_line + CSV_SEPARATOR.join(values)

    @staticmethod
    def to_compact(event: dict) -> str:
        """Ultra-compact format: seq|ts|delta|type|key|pos|buflen"""
        return COMPACT_SEPARATOR.join([
            str(event.get("seq", 0)),
            str(event.get("timestamp_ms", 0)),
            str(event.get("delta_ms", 0)),
            event.get("event_type", "?"),
            event.get("key", "?")[:1],
            str(event.get("cursor_pos", 0)),
            str(event.get("buffer_len", 0)),
        ])

    @staticmethod
    def to_sse(event: dict, event_name: str = "keystroke") -> str:
        """Server-Sent Events format."""
        data = json.dumps(event)
        return f"event: {event_name}\ndata: {data}\n\n"

    @classmethod
    def format_event(cls, event: dict, fmt: str = "json") -> str:
        formatters = {
            "json": cls.to_json,
            "json_pretty": cls.to_json_pretty,
            "csv": cls.to_csv,
            "compact": cls.to_compact,
            "sse": cls.to_sse,
        }
        formatter = formatters.get(fmt, cls.to_json)
        return formatter(event)


# ═══════════════════════════════════════════════════════════════════
# CONNECTION POOL
# ═══════════════════════════════════════════════════════════════════

class ConnectionPool:
    """Manages connected streaming clients."""

    def __init__(self, max_clients: int = MAX_CLIENTS):
        self.max_clients = max_clients
        self._clients: dict[str, StreamClient] = {}
        self._lock = threading.Lock()

    def connect(self, fmt: str = "json", filters: dict = None) -> StreamClient:
        with self._lock:
            if len(self._clients) >= self.max_clients:
                # evict oldest inactive client
                self._evict_oldest()

            client = StreamClient(
                client_id=uuid.uuid4().hex[:8],
                connected_at_ms=_now_ms(),
                format=fmt,
                filters=filters or {},
            )
            self._clients[client.client_id] = client
            return client

    def disconnect(self, client_id: str):
        with self._lock:
            if client_id in self._clients:
                self._clients[client_id].active = False
                del self._clients[client_id]

    def broadcast(self, event: dict):
        with self._lock:
            dead = []
            for cid, client in self._clients.items():
                if not client.active:
                    dead.append(cid)
                    continue
                if not client.matches_filter(event):
                    continue
                formatted = StreamFormatter.format_event(event, client.format)
                try:
                    client.queue.put_nowait(formatted)
                    client.events_sent += 1
                except _queue_mod.Full:
                    dead.append(cid)

            for cid in dead:
                del self._clients[cid]

    def client_count(self) -> int:
        with self._lock:
            return len(self._clients)

    def get_client(self, client_id: str) -> Optional[StreamClient]:
        with self._lock:
            return self._clients.get(client_id)

    def list_clients(self) -> list[dict]:
        with self._lock:
            return [
                {
                    "client_id": c.client_id,
                    "connected_at_ms": c.connected_at_ms,
                    "format": c.format,
                    "events_sent": c.events_sent,
                    "active": c.active,
                    "queue_size": c.queue.qsize(),
                }
                for c in self._clients.values()
            ]

    def _evict_oldest(self):
        if not self._clients:
            return
        oldest_id = min(self._clients, key=lambda k: self._clients[k].connected_at_ms)
        self._clients[oldest_id].active = False
        del self._clients[oldest_id]

    def send_heartbeat(self):
        now = _now_ms()
        heartbeat = {
            "schema": SCHEMA_VERSION,
            "event_type": "heartbeat",
            "timestamp_ms": now,
            "clients": self.client_count(),
        }
        self.broadcast(heartbeat)
        with self._lock:
            for c in self._clients.values():
                c.last_heartbeat_ms = now


# ═══════════════════════════════════════════════════════════════════
# EVENT AGGREGATOR
# ═══════════════════════════════════════════════════════════════════

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


# ═══════════════════════════════════════════════════════════════════
# METRICS COLLECTOR
# ═══════════════════════════════════════════════════════════════════

class MetricsCollector:
    """Collects and computes percentile metrics from event stream."""

    def __init__(self):
        self._delta_samples: deque = deque(maxlen=5000)
        self._wpm_samples: deque = deque(maxlen=500)
        self._hesitation_samples: deque = deque(maxlen=200)
        self._session_durations: list[int] = []
        self._total_events = 0
        self._total_submits = 0
        self._total_discards = 0

    def record_event(self, event: dict):
        self._total_events += 1
        delta = event.get("delta_ms", 0)
        if delta > 0:
            self._delta_samples.append(delta)

        etype = event.get("event_type", "")
        if etype == "submit":
            self._total_submits += 1
        elif etype in ("clear", "discard"):
            self._total_discards += 1

    def record_wpm(self, wpm: float):
        if wpm > 0:
            self._wpm_samples.append(wpm)

    def record_hesitation(self, score: float):
        self._hesitation_samples.append(score)

    def record_session_duration(self, duration_ms: int):
        self._session_durations.append(duration_ms)

    def _percentiles(self, data: list, targets: list[int] = None) -> dict:
        targets = targets or PERCENTILE_TARGETS
        if not data:
            return {f"p{t}": 0 for t in targets}
        sorted_data = sorted(data)
        result = {}
        for t in targets:
            idx = int(math.ceil(len(sorted_data) * t / 100)) - 1
            idx = max(0, min(idx, len(sorted_data) - 1))
            result[f"p{t}"] = sorted_data[idx]
        return result

    def get_delta_percentiles(self) -> dict:
        return self._percentiles(list(self._delta_samples))

    def get_wpm_percentiles(self) -> dict:
        return self._percentiles(list(self._wpm_samples))

    def get_summary(self) -> dict:
        delta_p = self.get_delta_percentiles()
        wpm_p = self.get_wpm_percentiles()

        avg_hes = 0.0
        if self._hesitation_samples:
            avg_hes = round(statistics.mean(self._hesitation_samples), 3)

        return {
            "total_events": self._total_events,
            "total_submits": self._total_submits,
            "total_discards": self._total_discards,
            "submit_rate": round(
                self._total_submits / max(self._total_submits + self._total_discards, 1), 3
            ),
            "delta_percentiles": delta_p,
            "wpm_percentiles": wpm_p,
            "avg_hesitation": avg_hes,
            "sample_counts": {
                "delta": len(self._delta_samples),
                "wpm": len(self._wpm_samples),
                "hesitation": len(self._hesitation_samples),
                "sessions": len(self._session_durations),
            },
        }


# ═══════════════════════════════════════════════════════════════════
# ALERT ENGINE
# ═══════════════════════════════════════════════════════════════════

class AlertEngine:
    """Detects anomalies in the event stream and fires alerts."""

    def __init__(self, thresholds: dict = None):
        self.thresholds = thresholds or dict(ALERT_THRESHOLDS)
        self._alerts: list[Alert] = []
        self._last_alert_time: dict[str, int] = {}
        self._consecutive_deletes = 0
        self._consecutive_discards = 0
        self._baseline_wpm: Optional[float] = None
        self._wpm_history: deque = deque(maxlen=20)

    def process_event(self, event: dict, aggregator: EventAggregator) -> Optional[Alert]:
        now = event.get("timestamp_ms", _now_ms())
        etype = event.get("event_type", "")
        delta = event.get("delta_ms", 0)

        # Check: long pause
        if delta > self.thresholds["pause_duration_ms"]:
            return self._fire_alert(
                "long_pause", "warning",
                f"Long pause detected: {delta}ms",
                now, {"delta_ms": delta}
            )

        # Check: deletion burst
        if etype in ("delete", "backspace"):
            self._consecutive_deletes += 1
            if self._consecutive_deletes >= self.thresholds["deletion_burst_length"]:
                alert = self._fire_alert(
                    "deletion_burst", "warning",
                    f"Deletion burst: {self._consecutive_deletes} consecutive deletes",
                    now, {"count": self._consecutive_deletes}
                )
                self._consecutive_deletes = 0
                return alert
        else:
            self._consecutive_deletes = 0

        # Check: WPM drop
        current_wpm = aggregator.compute_rolling_wpm(5000)
        if current_wpm > 0:
            self._wpm_history.append(current_wpm)
            if self._baseline_wpm is None and len(self._wpm_history) >= 5:
                self._baseline_wpm = statistics.median(list(self._wpm_history))
            elif self._baseline_wpm and self._baseline_wpm > 0:
                drop_pct = ((self._baseline_wpm - current_wpm) / self._baseline_wpm) * 100
                if drop_pct > self.thresholds["wpm_drop_percent"]:
                    return self._fire_alert(
                        "wpm_drop", "info",
                        f"WPM dropped {drop_pct:.0f}%: {self._baseline_wpm:.0f} → {current_wpm:.0f}",
                        now, {"baseline": self._baseline_wpm, "current": current_wpm}
                    )

        # Check: discard streak
        if etype in ("clear", "discard"):
            self._consecutive_discards += 1
            if self._consecutive_discards >= self.thresholds["discard_streak"]:
                alert = self._fire_alert(
                    "discard_streak", "critical",
                    f"Discard streak: {self._consecutive_discards} messages abandoned",
                    now, {"count": self._consecutive_discards}
                )
                return alert
        elif etype == "submit":
            self._consecutive_discards = 0

        return None

    def process_hesitation(self, score: float) -> Optional[Alert]:
        if score > self.thresholds["hesitation_score"]:
            return self._fire_alert(
                "high_hesitation", "warning",
                f"High hesitation score: {score}",
                _now_ms(), {"score": score}
            )
        return None

    def _fire_alert(self, alert_type: str, severity: str, message: str,
                    timestamp_ms: int, context: dict) -> Optional[Alert]:
        # cooldown check
        last = self._last_alert_time.get(alert_type, 0)
        if timestamp_ms - last < ALERT_COOLDOWN_MS:
            return None

        alert = Alert(
            alert_id=uuid.uuid4().hex[:8],
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp_ms=timestamp_ms,
            context=context,
        )
        self._alerts.append(alert)
        self._last_alert_time[alert_type] = timestamp_ms
        return alert

    def get_alerts(self, limit: int = 50) -> list[dict]:
        return [asdict(a) for a in self._alerts[-limit:]]

    def unacknowledged_count(self) -> int:
        return sum(1 for a in self._alerts if not a.acknowledged)

    def acknowledge(self, alert_id: str) -> bool:
        for a in self._alerts:
            if a.alert_id == alert_id:
                a.acknowledged = True
                return True
        return False

    def clear_alerts(self):
        self._alerts.clear()
        self._last_alert_time.clear()


# ═══════════════════════════════════════════════════════════════════
# SESSION REPLAY
# ═══════════════════════════════════════════════════════════════════

class SessionReplay:
    """Replays a session from JSONL file at real-time or accelerated speed."""

    def __init__(self, events_file: str):
        self.events_file = Path(events_file)
        self._events: list[dict] = []
        self._loaded = False

    def load(self):
        if not self.events_file.exists():
            raise FileNotFoundError(f"Events file not found: {self.events_file}")
        self._events = []
        with open(self.events_file, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= MAX_REPLAY_EVENTS:
                    break
                self._events.append(json.loads(line))
        self._loaded = True

    def event_count(self) -> int:
        return len(self._events)

    def duration_ms(self) -> int:
        if len(self._events) < 2:
            return 0
        return self._events[-1]["timestamp_ms"] - self._events[0]["timestamp_ms"]

    def replay(self, speed: float = 1.0, callback: Callable = None):
        """Replay events with timing. speed=2.0 means 2x faster."""
        if not self._loaded:
            self.load()

        if not self._events:
            return

        callback = callback or (lambda e: print(json.dumps(e, indent=2)))
        prev_ts = self._events[0]["timestamp_ms"]

        for event in self._events:
            ts = event["timestamp_ms"]
            gap_ms = ts - prev_ts
            if gap_ms > 0 and speed > 0:
                time.sleep((gap_ms / 1000) / speed)
            callback(event)
            prev_ts = ts

    def get_events(self, start: int = 0, count: int = 100) -> list[dict]:
        return self._events[start:start + count]

    def find_by_message(self, message_id: str) -> list[dict]:
        return [e for e in self._events if e.get("message_id") == message_id]

    def get_message_ids(self) -> list[str]:
        seen = []
        for e in self._events:
            mid = e.get("message_id")
            if mid and mid not in seen:
                seen.append(mid)
        return seen

    def summarize_messages(self) -> list[dict]:
        """Per-message summary from raw events."""
        messages = {}
        for e in self._events:
            mid = e.get("message_id", "unknown")
            if mid not in messages:
                messages[mid] = {
                    "message_id": mid,
                    "first_ts": e["timestamp_ms"],
                    "last_ts": e["timestamp_ms"],
                    "events": 0,
                    "inserts": 0,
                    "deletes": 0,
                    "pastes": 0,
                    "final_buffer": "",
                }
            m = messages[mid]
            m["events"] += 1
            m["last_ts"] = e["timestamp_ms"]
            m["final_buffer"] = e.get("buffer", "")
            etype = e.get("event_type", "")
            if etype == "insert":
                m["inserts"] += 1
            elif etype in ("delete", "backspace"):
                m["deletes"] += 1
            elif etype == "paste":
                m["pastes"] += 1

        for m in messages.values():
            m["duration_ms"] = m["last_ts"] - m["first_ts"]
            total = m["inserts"] + m["deletes"]
            m["deletion_ratio"] = round(m["deletes"] / max(total, 1), 3)

        return list(messages.values())


# ═══════════════════════════════════════════════════════════════════
# LIVE DASHBOARD
# ═══════════════════════════════════════════════════════════════════

class LiveDashboard:
    """Terminal-based live dashboard that prints rolling stats."""

    def __init__(self, aggregator: EventAggregator, metrics: MetricsCollector,
                 alerts: AlertEngine, pool: ConnectionPool):
        self.aggregator = aggregator
        self.metrics = metrics
        self.alerts = alerts
        self.pool = pool
        self._refresh_count = 0

    def render(self) -> str:
        self._refresh_count += 1
        snap = self.aggregator.get_snapshot()
        summary = self.metrics.get_summary()
        alert_list = self.alerts.get_alerts(5)
        clients = self.pool.client_count()

        lines = []
        lines.append("╔══════════════════════════════════════════════════════╗")
        lines.append("║         KEYSTROKE TELEMETRY — LIVE DASHBOARD        ║")
        lines.append(f"║  Refresh #{self._refresh_count:<6}  Clients: {clients:<4}  "
                     f"Events: {summary['total_events']:<8} ║")
        lines.append("╠══════════════════════════════════════════════════════╣")

        # Rolling windows
        for ws_key, ws_data in snap.get("windows", {}).items():
            ws_sec = int(ws_key) // 1000
            lines.append(f"║  [{ws_sec}s window] events={ws_data['event_count']:<5} "
                         f"wpm={ws_data['estimated_wpm']:<6} "
                         f"del%={ws_data['deletion_ratio']:<5}   ║")

        lines.append("╠══════════════════════════════════════════════════════╣")

        # Percentiles
        dp = summary.get("delta_percentiles", {})
        lines.append(f"║  Delta P50={dp.get('p50',0):<5} P90={dp.get('p90',0):<5} "
                     f"P99={dp.get('p99',0):<8}        ║")

        wp = summary.get("wpm_percentiles", {})
        lines.append(f"║  WPM   P50={wp.get('p50',0):<5} P90={wp.get('p90',0):<5} "
                     f"P99={wp.get('p99',0):<8}        ║")

        lines.append(f"║  Submit rate: {summary.get('submit_rate', 0):<6} "
                     f"Avg hesitation: {summary.get('avg_hesitation', 0):<6}    ║")

        # Alerts
        if alert_list:
            lines.append("╠══════════════════════════════════════════════════════╣")
            lines.append("║  ALERTS:                                             ║")
            for a in alert_list[-3:]:
                sev = a["severity"].upper()[:4]
                msg = a["message"][:40]
                lines.append(f"║  [{sev}] {msg:<45} ║")

        lines.append("╚══════════════════════════════════════════════════════╝")
        return "\n".join(lines)

    def print_dashboard(self):
        output = self.render()
        # Clear terminal and print
        print("\033[2J\033[H" + output)

    def render_compact(self) -> str:
        snap = self.aggregator.get_snapshot()
        w5 = snap.get("windows", {}).get("5000", {})
        return (f"[LIVE] events={w5.get('event_count', 0)} "
                f"wpm={w5.get('estimated_wpm', 0)} "
                f"del%={w5.get('deletion_ratio', 0)} "
                f"clients={self.pool.client_count()}")


# ═══════════════════════════════════════════════════════════════════
# HTTP REQUEST HANDLER (SSE endpoint)
# ═══════════════════════════════════════════════════════════════════

class TelemetryHTTPHandler(BaseHTTPRequestHandler):
    """Handles HTTP requests for the streaming telemetry server."""

    server_ref = None  # set by StreamingTelemetryServer

    def do_GET(self):
        if self.path == "/stream":
            self._handle_stream()
        elif self.path == "/dashboard":
            self._handle_dashboard()
        elif self.path == "/metrics":
            self._handle_metrics()
        elif self.path == "/alerts":
            self._handle_alerts()
        elif self.path == "/replay":
            self._handle_replay_list()
        elif self.path.startswith("/replay/"):
            self._handle_replay_session()
        elif self.path == "/health":
            self._handle_health()
        else:
            self.send_error(404)

    def _handle_stream(self):
        server = self.__class__.server_ref
        if not server:
            self.send_error(503)
            return

        client = server.pool.connect(fmt="sse")
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        try:
            while client.active:
                try:
                    data = client.queue.get(timeout=1.0)
                    self.wfile.write(data.encode("utf-8"))
                    self.wfile.flush()
                except _queue_mod.Empty:
                    # send keepalive comment
                    self.wfile.write(b": keepalive\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            server.pool.disconnect(client.client_id)

    def _handle_dashboard(self):
        server = self.__class__.server_ref
        if not server:
            self.send_error(503)
            return
        output = server.dashboard.render()
        self._send_json_response({"dashboard": output})

    def _handle_metrics(self):
        server = self.__class__.server_ref
        if not server:
            self.send_error(503)
            return
        self._send_json_response(server.metrics.get_summary())

    def _handle_alerts(self):
        server = self.__class__.server_ref
        if not server:
            self.send_error(503)
            return
        self._send_json_response({
            "alerts": server.alert_engine.get_alerts(),
            "unacknowledged": server.alert_engine.unacknowledged_count(),
        })

    def _handle_replay_list(self):
        server = self.__class__.server_ref
        if not server:
            self.send_error(503)
            return
        log_dir = Path(server.logger.log_dir)
        files = sorted(log_dir.glob("events_*.jsonl"))
        self._send_json_response({
            "sessions": [{"file": f.name, "size": f.stat().st_size} for f in files]
        })

    def _handle_replay_session(self):
        server = self.__class__.server_ref
        if not server:
            self.send_error(503)
            return
        session_id = self.path.split("/replay/", 1)[1]
        events_file = Path(server.logger.log_dir) / f"events_{session_id}.jsonl"
        if not events_file.exists():
            self.send_error(404)
            return
        replay = SessionReplay(str(events_file))
        replay.load()
        self._send_json_response({
            "session_id": session_id,
            "event_count": replay.event_count(),
            "duration_ms": replay.duration_ms(),
            "messages": replay.summarize_messages(),
        })

    def _handle_health(self):
        self._send_json_response({"status": "ok", "timestamp_ms": _now_ms()})

    def _send_json_response(self, data: dict, status: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # suppress default logging


# ═══════════════════════════════════════════════════════════════════
# STREAMING TELEMETRY SERVER (orchestrator)
# ═══════════════════════════════════════════════════════════════════

class StreamingTelemetryServer:
    """Main orchestrator: wraps TelemetryLogger with live streaming,
    aggregation, metrics, alerts, and an HTTP endpoint."""

    def __init__(self, log_dir: str = "logs", port: int = DEFAULT_PORT,
                 live_print: bool = True):
        self.port = port
        self.logger = TelemetryLogger(log_dir=log_dir, live_print=live_print)
        self.pool = ConnectionPool()
        self.aggregator = EventAggregator()
        self.metrics = MetricsCollector()
        self.alert_engine = AlertEngine()
        self.dashboard = LiveDashboard(self.aggregator, self.metrics,
                                        self.alert_engine, self.pool)
        self._http_server: Optional[HTTPServer] = None
        self._http_thread: Optional[threading.Thread] = None
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._running = False

    def start(self):
        """Start HTTP server and heartbeat in background threads."""
        self._running = True

        TelemetryHTTPHandler.server_ref = self
        self._http_server = HTTPServer(("127.0.0.1", self.port), TelemetryHTTPHandler)
        self._http_thread = threading.Thread(target=self._http_server.serve_forever, daemon=True)
        self._http_thread.start()

        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()

        print(f"[SERVER] Streaming at http://127.0.0.1:{self.port}")
        print(f"[SERVER] Endpoints: /stream /dashboard /metrics /alerts /replay /health")

    def stop(self):
        self._running = False
        if self._http_server:
            self._http_server.shutdown()
        self.logger.close()
        print("[SERVER] Stopped")

    def log_event(self, event_type: str, key: str, cursor_pos: int, buffer_text: str):
        """Log event through all layers: logger → aggregator → metrics → alerts → broadcast."""
        self.logger.log_event(event_type, key, cursor_pos, buffer_text)

        # reconstruct the block for aggregation/broadcast
        # (the logger already wrote it to file and printed it)
        block = {
            "schema": SCHEMA_VERSION,
            "seq": self.logger._event_seq,
            "session_id": self.logger.session_id,
            "message_id": self.logger.current_message_id,
            "timestamp_ms": self.logger.last_event_time_ms,
            "delta_ms": 0,  # approximate; real delta was already logged
            "event_type": event_type,
            "key": key,
            "cursor_pos": cursor_pos,
            "buffer": buffer_text,
            "buffer_len": len(buffer_text),
        }

        self.aggregator.ingest(block)
        self.metrics.record_event(block)

        # Update rolling WPM
        wpm = self.aggregator.compute_rolling_wpm()
        self.metrics.record_wpm(wpm)

        # Check for alerts
        alert = self.alert_engine.process_event(block, self.aggregator)
        if alert:
            alert_block = {
                "schema": SCHEMA_VERSION,
                "event_type": "alert",
                "alert": asdict(alert),
                "timestamp_ms": alert.timestamp_ms,
            }
            self.pool.broadcast(alert_block)

        # Broadcast the event to all connected clients
        self.pool.broadcast(block)

    def start_message(self) -> str:
        return self.logger.start_message()

    def submit_message(self, final_text: str):
        self.logger.submit_message(final_text)
        # Record hesitation
        if self.logger.all_summaries:
            last = self.logger.all_summaries[-1]
            hes = last.get("hesitation_score", 0)
            self.metrics.record_hesitation(hes)
            self.alert_engine.process_hesitation(hes)

    def discard_message(self, buffer_text: str):
        self.logger.discard_message(buffer_text)
        if self.logger.all_summaries:
            last = self.logger.all_summaries[-1]
            hes = last.get("hesitation_score", 0)
            self.metrics.record_hesitation(hes)
            self.alert_engine.process_hesitation(hes)

    def get_dashboard(self) -> str:
        return self.dashboard.render()

    def get_compact_status(self) -> str:
        return self.dashboard.render_compact()

    def _heartbeat_loop(self):
        while self._running:
            time.sleep(HEARTBEAT_INTERVAL_MS / 1000)
            self.pool.send_heartbeat()


# ═══════════════════════════════════════════════════════════════════
# STANDALONE TEST / DEMO
# ═══════════════════════════════════════════════════════════════════

def _sim_type(server, text, buf="", wpm=80):
    delay = 60.0 / (wpm * 5)
    for ch in text:
        buf += ch
        server.log_event("insert", ch, len(buf), buf)
        time.sleep(delay)
    return buf

def _sim_backspace(server, buf, count=1):
    for _ in range(count):
        if buf:
            removed = buf[-1]
            buf = buf[:-1]
            server.log_event("backspace", removed, len(buf), buf)
            time.sleep(0.03)
    return buf


def run_demo():
    """Run a standalone demo of the streaming server."""
    print("=" * 60)
    print("  STREAMING TELEMETRY DEMO")
    print("=" * 60)

    server = StreamingTelemetryServer(log_dir="demo_logs", port=8787, live_print=False)
    server.start()

    time.sleep(0.5)

    # Simulate typing
    server.start_message()
    buf = _sim_type(server, "Hello world, this is a test of the streaming layer")
    server.submit_message(buf)

    time.sleep(0.3)

    # Simulate typo + correction
    server.start_message()
    buf = _sim_type(server, "Waht is the ")  # typo
    buf = _sim_backspace(server, buf, 12)     # delete it all
    buf = _sim_type(server, "What is the meaning of everything?", buf)
    server.submit_message(buf)

    time.sleep(0.3)

    # Simulate discard
    server.start_message()
    buf = _sim_type(server, "Actually never mind this whole thing")
    server.discard_message(buf)

    time.sleep(0.5)

    # Print dashboard
    print("\n" + server.get_dashboard())

    # Print metrics
    print("\nMETRICS:")
    print(json.dumps(server.metrics.get_summary(), indent=2))

    # Print alerts
    alerts = server.alert_engine.get_alerts()
    if alerts:
        print(f"\nALERTS ({len(alerts)}):")
        for a in alerts:
            print(f"  [{a['severity']}] {a['message']}")

    # Print aggregation snapshot
    print("\nAGGREGATION:")
    snap = server.aggregator.get_snapshot()
    for ws, data in snap["windows"].items():
        print(f"  [{int(ws)//1000}s] events={data['event_count']} wpm={data['estimated_wpm']} "
              f"del%={data['deletion_ratio']}")

    # Test replay
    print("\nREPLAY:")
    replay = SessionReplay(str(server.logger.events_file))
    replay.load()
    print(f"  Events: {replay.event_count()}")
    print(f"  Duration: {replay.duration_ms()}ms")
    msgs = replay.summarize_messages()
    for m in msgs:
        print(f"  [{m['message_id'][:8]}] {m['events']} events, "
              f"del%={m['deletion_ratio']}, dur={m['duration_ms']}ms")

    server.stop()

    print("\n" + "=" * 60)
    print("  DEMO COMPLETE ✓")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
