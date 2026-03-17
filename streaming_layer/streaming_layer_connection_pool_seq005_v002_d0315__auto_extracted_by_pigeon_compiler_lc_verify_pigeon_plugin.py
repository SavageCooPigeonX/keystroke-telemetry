"""streaming_layer_connection_pool_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v002 | 107 lines | ~932 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: verify_pigeon_plugin
# LAST:   2026-03-15 @ caac48c
# SESSIONS: 1
# ──────────────────────────────────────────────
from src.logger_seq003_v003_d0317__core_keystroke_telemetry_logger_lc_pulse_telemetry_prompt import TelemetryLogger, SCHEMA_VERSION
from src.timestamp_utils_seq001_v003_d0317__millisecond_epoch_timestamp_utility_lc_pulse_telemetry_prompt import _now_ms
from typing import Optional, Callable
import json
import queue as _queue_mod
import threading
import time
import uuid

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
