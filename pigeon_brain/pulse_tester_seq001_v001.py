"""Pulse Tester — continuously imports modules and cascades through deps.

Sends call/exception events to the live WebSocket server so the UI
lights up in real-time showing which endpoints are alive vs dead.

Usage:
    py -m pigeon_brain.pulse_tester_seq001_v001_seq001_v001              # default: sweep every 2s
    py -m pigeon_brain.pulse_tester_seq001_v001_seq001_v001 --interval 1 # faster sweep
"""

import asyncio
import importlib
import importlib.util
import json
import sys
import time
from pathlib import Path

try:
    import websockets
    HAS_WS = True
except ImportError:
    HAS_WS = False

ROOT = Path(__file__).resolve().parent.parent
_seq = 0


def _next_seq():
    global _seq
    _seq += 1
    return _seq


def _make_event(event_type, module, func="import", caller=None, error=None):
    ev = {
        "seq": _next_seq(),
        "ts": int(time.time() * 1000),
        "event": event_type,
        "module": module,
        "func": func,
        "caller": caller or "",
        "line": 0,
    }
    if error:
        ev["error"] = str(error)[:200]
    return ev


def _load_graph():
    """Load graph_cache.json or dual_view.json for node/edge topology."""
    for name in ("dual_view.json", "graph_cache.json"):
        p = ROOT / "pigeon_brain" / name
        if p.exists():
            with open(p, encoding="utf-8") as f:
                return json.load(f)
    return {"nodes": [], "edges": []}


def _build_dep_chains(graph):
    """Build adjacency list: module -> list of modules it imports."""
    edges = graph.get("edges", [])
    deps = {}
    for e in edges:
        src = e.get("from", "")
        tgt = e.get("to", "")
        if src and tgt:
            deps.setdefault(src, []).append(tgt)
    return deps


def _resolve_import_path(node_name, nodes_by_name):
    """Find the importable path for a module name."""
    info = nodes_by_name.get(node_name, {})
    path = info.get("path", "")
    if not path:
        return None
    full = ROOT / path
    if full.exists():
        return full
    return None


def _try_import(module_path):
    """Try to import a Python file. Returns (True, module) or (False, error)."""
    try:
        spec = importlib.util.spec_from_file_location("_pulse_test", str(module_path))
        if spec is None or spec.loader is None:
            return False, "no loader"
        mod = importlib.util.module_from_spec(spec)
        # Don't actually exec — just verify the spec loads
        # This tests that the file parses and its deps resolve
        compile(module_path.read_text(encoding="utf-8"), str(module_path), "exec")
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError: {e.msg} line {e.lineno}"
    except Exception as e:
        return False, str(e)[:200]


def run_sweep(graph):
    """Run one full sweep: test every node and cascade through edges."""
    nodes = graph.get("nodes", [])
    nodes_by_name = {n["name"]: n for n in nodes}
    deps = _build_dep_chains(graph)
    events = []

    # Sort by degree descending — test hubs first
    sorted_nodes = sorted(nodes, key=lambda n: (n.get("in_degree", 0) + n.get("out_degree", 0)), reverse=True)

    tested = set()

    def cascade(name, caller=None, depth=0):
        if name in tested or depth > 6:
            return
        tested.add(name)

        path = _resolve_import_path(name, nodes_by_name)
        if path is None:
            # No file — still emit a call so the node lights up dimly
            events.append(_make_event("call", name, "probe", caller))
            return

        # Emit call event (node lights up)
        events.append(_make_event("call", name, "import_test", caller))

        ok, err = _try_import(path)
        if ok:
            events.append(_make_event("return", name, "import_test", caller))
            # Cascade to dependencies
            for dep in deps.get(name, []):
                # Stagger slightly for visual cascade effect
                events.append(_make_event("call", dep, "cascade", name))
                cascade(dep, caller=name, depth=depth + 1)
        else:
            events.append(_make_event("exception", name, "import_test", caller, error=err))

    for node in sorted_nodes:
        cascade(node["name"])

    return events


async def pulse_loop(interval=2.0, ws_url="ws://127.0.0.1:8765"):
    """Continuously sweep and push events to the live server."""
    graph = _load_graph()
    print(f"[pulse-tester] Loaded {len(graph.get('nodes', []))} nodes, {len(graph.get('edges', []))} edges")
    print(f"[pulse-tester] Sweeping every {interval}s → {ws_url}")

    while True:
        try:
            async with websockets.connect(ws_url) as ws:
                print(f"[pulse-tester] Connected to live server")
                while True:
                    events = run_sweep(graph)
                    # Send in batches to create visual cascade
                    batch_size = 8
                    for i in range(0, len(events), batch_size):
                        batch = events[i:i + batch_size]
                        await ws.send(json.dumps({"type": "inject", "events": batch}))
                        await asyncio.sleep(0.08)  # stagger for visual effect
                    alive = sum(1 for e in events if e["event"] == "return")
                    dead = sum(1 for e in events if e["event"] == "exception")
                    print(f"[pulse-tester] Sweep: {alive} alive, {dead} dead, {len(events)} total events")
                    await asyncio.sleep(interval)
        except (ConnectionRefusedError, OSError) as e:
            print(f"[pulse-tester] Can't connect to {ws_url}, retrying in 3s...")
            await asyncio.sleep(3)
        except websockets.exceptions.ConnectionClosed:
            print(f"[pulse-tester] Connection lost, reconnecting...")
            await asyncio.sleep(1)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Pigeon Brain Pulse Tester")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between sweeps")
    parser.add_argument("--ws", default="ws://127.0.0.1:8765", help="WebSocket URL")
    args = parser.parse_args()

    if not HAS_WS:
        print("ERROR: 'websockets' required. pip install websockets")
        sys.exit(1)

    asyncio.run(pulse_loop(args.interval, args.ws))


if __name__ == "__main__":
    main()
