"""streaming_layer_http_handler_seq011_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 011 | VER: v002 | 135 lines | ~1,184 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: verify_pigeon_plugin
# LAST:   2026-03-15 @ caac48c
# SESSIONS: 1
# ──────────────────────────────────────────────
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from src.timestamp_utils_seq001_v003_d0317__millisecond_epoch_timestamp_utility_lc_pulse_telemetry_prompt import _now_ms
import json
import queue as _queue_mod
import time

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
