# @pigeon: seq=013 | role=traced_runner | depends=[trace_hook,live_server] | exports=[run_traced] | tokens=~350
"""Run any Python script with the pigeon trace hook active.

Events are pushed to the live WebSocket server for real-time visualization.
The server must already be running (`py -m pigeon_brain live`).

Usage:
    py -m pigeon_brain.traced_runner test_all.py
    py -m pigeon_brain.traced_runner stress_test.py
"""

# ── pigeon ────────────────────────────────────
# SEQ: 013 | VER: v002 | 102 lines | ~872 tokens
# DESC:   run_any_python_script_with
# INTENT: pigeon_brain_system
# LAST:   2026-03-23 @ 465cbfa
# SESSIONS: 1
# ──────────────────────────────────────────────

import importlib.util
import json
import sys
import time
from pathlib import Path

# Try to connect to the live server to push events
try:
    import websockets
    import websockets.sync.client
    HAS_WS = True
except ImportError:
    HAS_WS = False


def run_traced(script_path: str, root: Path = None):
    """Run a script with trace hook active, pushing events to live server."""
    root = root or Path(".")
    script = Path(script_path).resolve()
    if not script.exists():
        print(f"Error: {script} not found")
        return

    from pigeon_brain.trace_hook_seq011_v002_d0323__instruments_python_calls_between_pigeon_lc_pigeon_brain_system import start_trace, stop_trace, drain_events

    # Start tracing
    start_trace(root)
    print(f"[traced] Trace hook active — running {script.name}")
    print(f"[traced] If live server is running, events appear in real-time")

    # Background thread to push events to WebSocket server
    ws_pusher = None
    if HAS_WS:
        import threading

        def _push_loop():
            """Connect to WS server and push events periodically."""
            try:
                ws = websockets.sync.client.connect("ws://127.0.0.1:8765")
                while True:
                    events = drain_events(200)
                    if events:
                        ws.send(json.dumps({"type": "inject", "events": events}))
                    time.sleep(0.05)
            except Exception:
                pass  # Server not running — events just accumulate

        ws_pusher = threading.Thread(target=_push_loop, daemon=True)
        ws_pusher.start()

    # Execute the script
    start_time = time.time()
    try:
        # Load and exec the script in its own namespace
        spec = importlib.util.spec_from_file_location("__traced__", str(script))
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            sys.modules["__traced__"] = mod
            spec.loader.exec_module(mod)
    except SystemExit:
        pass  # Script called sys.exit()
    except Exception as e:
        print(f"[traced] Script error: {e}")
    finally:
        elapsed = time.time() - start_time
        stop_trace()

        # Drain any remaining events and report
        remaining = drain_events(5000)
        total = len(remaining)
        modules_seen = set()
        for ev in remaining:
            if ev.get("module"):
                modules_seen.add(ev["module"])

        print(f"\n[traced] Done in {elapsed:.2f}s")
        print(f"[traced] {total} events captured, {len(modules_seen)} modules touched")

        # Write events to file for offline analysis
        out = root / "pigeon_brain" / "trace_log.jsonl"
        with open(out, "w", encoding="utf-8") as f:
            for ev in remaining:
                f.write(json.dumps(ev) + "\n")
        print(f"[traced] Events saved to {out}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: py -m pigeon_brain.traced_runner <script.py>")
        sys.exit(1)
    run_traced(sys.argv[1])
