"""WebSocket server for live execution tracing.

Pushes trace events to connected browser clients in real-time.
Also serves a /snapshot endpoint via HTTP for initial graph state.

Usage:
    py -m pigeon_brain live          # start server + trace hook
    py -m pigeon_brain live --port 8765
"""


import asyncio
import json
import os
import signal
import sys
import threading
import time
from pathlib import Path

# Optional websockets dependency — fall back to built-in HTTP if missing
try:
    import websockets
    import websockets.server
    HAS_WS = True
except ImportError:
    HAS_WS = False

from pigeon_brain.钩w_th_s011_v002_d0323_缩分话_λP import (
    drain_events,
    peek_recent,
    start_trace,
    stop_trace,
)
from pigeon_brain.node_tester import test_node as _run_node_tests
from pigeon_brain.gemini_chat import (
    chat as _gemini_chat,
    parse_file_actions,
    execute_file_action,
    strip_action_blocks,
)

_clients = set()
_injected = []  # Events injected by external traced_runner processes
_inject_lock = threading.Lock()
_project_root = Path(".")  # Set during serve_live
_chat_histories = {}  # ws_id -> list of {role, text}


async def _ws_handler(websocket):
    """Handle a single WebSocket client connection."""
    _clients.add(websocket)
    try:
        # Send recent history on connect
        recent = peek_recent(100)
        if recent:
            await websocket.send(json.dumps({"type": "history", "events": recent}))
        # Listen for commands from UI
        async for msg in websocket:
            try:
                data = json.loads(msg)
                if data.get("type") == "inject" and data.get("events"):
                    with _inject_lock:
                        _injected.extend(data["events"])
                elif data.get("type") == "test_node" and data.get("node"):
                    # Run real tests on the tapped node, inject results
                    loop = asyncio.get_event_loop()
                    test_results = await loop.run_in_executor(
                        None, _run_node_tests, _project_root, data["node"]
                    )
                    if test_results:
                        with _inject_lock:
                            _injected.extend(test_results)
                elif data.get("type") == "chat" and data.get("message"):
                    ws_id = id(websocket)
                    if ws_id not in _chat_histories:
                        _chat_histories[ws_id] = []
                    if data.get("clear"):
                        _chat_histories[ws_id] = []
                    _chat_histories[ws_id].append({"role": "user", "text": data["message"]})
                    selected = data.get("selectedNode")
                    loop = asyncio.get_event_loop()
                    reply = await loop.run_in_executor(
                        None, _gemini_chat, _project_root,
                        list(_chat_histories[ws_id]), selected
                    )
                    # Parse and execute file-write actions from Gemini response
                    file_actions = parse_file_actions(reply)
                    file_results = []
                    for action in file_actions:
                        result = execute_file_action(_project_root, action)
                        file_results.append(result)
                    # Clean display text (strip action blocks)
                    display_text = strip_action_blocks(reply) if file_actions else reply
                    _chat_histories[ws_id].append({"role": "model", "text": display_text})
                    # Keep history bounded
                    if len(_chat_histories[ws_id]) > 40:
                        _chat_histories[ws_id] = _chat_histories[ws_id][-30:]
                    await websocket.send(json.dumps({
                        "type": "chat_response",
                        "text": display_text,
                        "file_actions": file_results if file_results else None,
                    }))
            except Exception:
                pass
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        _clients.discard(websocket)


async def _broadcast_loop():
    """Drain the trace buffer + injected events and broadcast to all connected clients."""
    while True:
        events = drain_events(200)
        # Also grab injected events from external processes
        with _inject_lock:
            if _injected:
                events.extend(_injected)
                _injected.clear()
        if events and _clients:
            payload = json.dumps({"type": "events", "events": events})
            dead = set()
            for ws in _clients.copy():
                try:
                    await ws.send(payload)
                except Exception:
                    dead.add(ws)
            _clients -= dead
        await asyncio.sleep(0.05)  # 50ms — 20 pushes/sec


async def _snapshot_server(root: Path, host: str, port: int):
    """Minimal HTTP server for /snapshot (initial dual_view.json)."""
    from http.server import HTTPServer, BaseHTTPRequestHandler

    dual_path = root / "pigeon_brain" / "dual_view.json"

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            # CORS
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            if self.path == "/snapshot":
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                if dual_path.exists():
                    self.wfile.write(dual_path.read_bytes())
                else:
                    self.wfile.write(b'{}')
            elif self.path == "/events":
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(peek_recent(100)).encode())
            else:
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"pigeon-brain live server")

        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def log_message(self, format, *args):
            pass  # Silence HTTP logs

    server = HTTPServer((host, port), Handler)
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, server.serve_forever)


async def run_server(root: Path, ws_port: int = 8765, http_port: int = 8766):
    """Start WebSocket + HTTP servers and trace hook."""
    global _project_root
    _project_root = root

    if not HAS_WS:
        print("ERROR: 'websockets' package required. Install with: pip install websockets")
        return

    # Start trace hook
    start_trace(root)
    print(f"[pigeon-brain] Trace hook active — monitoring {len(drain_events(0)) or 'all'} modules")

    # HTTP snapshot server in background thread
    http_thread = threading.Thread(
        target=lambda: _run_http_sync(root, "127.0.0.1", http_port),
        daemon=True,
    )
    http_thread.start()
    print(f"[pigeon-brain] HTTP snapshot: http://127.0.0.1:{http_port}/snapshot")

    # WebSocket server
    broadcast_task = asyncio.create_task(_broadcast_loop())
    async with websockets.server.serve(_ws_handler, "127.0.0.1", ws_port):
        print(f"[pigeon-brain] WebSocket live: ws://127.0.0.1:{ws_port}")
        print(f"[pigeon-brain] Ready — run your code in another terminal")
        await asyncio.Future()  # Block forever


def _run_http_sync(root, host, port):
    """Synchronous HTTP server for background thread."""
    from http.server import HTTPServer, BaseHTTPRequestHandler

    dual_path = root / "pigeon_brain" / "dual_view.json"

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            if self.path == "/snapshot":
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                if dual_path.exists():
                    self.wfile.write(dual_path.read_bytes())
                else:
                    self.wfile.write(b'{}')
            elif self.path == "/events":
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(peek_recent(100)).encode())
            else:
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"pigeon-brain live server")

        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def log_message(self, format, *args):
            pass

    server = HTTPServer((host, port), Handler)
    server.serve_forever()


def serve_live(root: Path, ws_port: int = 8765, http_port: int = 8766):
    """Entry point for CLI."""
    try:
        asyncio.run(run_server(root, ws_port, http_port))
    except KeyboardInterrupt:
        stop_trace()
        print("\n[pigeon-brain] Stopped.")
