"""streaming_layer_orchestrator_seq016_v001.py — Pigeon-extracted by compiler."""
from dataclasses import dataclass, field, asdict
from http.server import HTTPServer, BaseHTTPRequestHandler
from src.logger_seq003_v001 import TelemetryLogger, SCHEMA_VERSION
from typing import Optional, Callable
import os
import threading
import time

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
