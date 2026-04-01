# @pigeon: seq=011 | role=trace_hook | depends=[models,graph_extractor] | exports=[start_trace,stop_trace] | tokens=~600
"""Live execution trace hook — instruments Python calls between pigeon modules.

Uses sys.settrace to capture real inter-module call/return events and writes
them to a shared event buffer. The WebSocket server reads this buffer and
pushes events to the UI in real-time.

Usage:
    from pigeon_brain.trace_hook_seq011_v002_d0323__钩令_instruments_python_calls_between_pigeon_lc_pigeon_brain_system import start_trace, stop_trace
    start_trace(root)
    # ... run code ...
    stop_trace()
"""

# ── pigeon ────────────────────────────────────
# SEQ: 011 | VER: v002 | 137 lines | ~976 tokens
# DESC:   instruments_python_calls_between_pigeon
# INTENT: pigeon_brain_system
# LAST:   2026-03-23 @ 465cbfa
# SESSIONS: 1
# ──────────────────────────────────────────────

import json
import os
import sys
import threading
import time
from collections import deque
from pathlib import Path

# Shared event buffer — WebSocket server reads from here
_event_buffer = deque(maxlen=5000)
_trace_active = False
_module_map = {}   # abs_path -> module_name
_seq_counter = 0
_lock = threading.Lock()
_root = None


def start_trace(root: Path):
    """Begin tracing inter-module calls."""
    global _trace_active, _module_map, _seq_counter, _root
    _root = root.resolve()
    _module_map = _build_module_map(root)
    _seq_counter = 0
    _trace_active = True
    sys.settrace(_trace_fn)
    threading.settrace(_trace_fn)


def stop_trace():
    """Stop tracing."""
    global _trace_active
    _trace_active = False
    sys.settrace(None)
    threading.settrace(None)


def drain_events(max_n=200):
    """Drain up to max_n events from the buffer. Non-blocking."""
    events = []
    with _lock:
        while _event_buffer and len(events) < max_n:
            events.append(_event_buffer.popleft())
    return events


def peek_recent(n=50):
    """Peek at the most recent n events without removing them."""
    with _lock:
        items = list(_event_buffer)
    return items[-n:]


def _build_module_map(root: Path) -> dict:
    """Map absolute file paths to pigeon module names."""
    registry_path = root / "pigeon_registry.json"
    if not registry_path.exists():
        return {}
    try:
        registry = json.loads(registry_path.read_text("utf-8"))
    except Exception:
        return {}

    mapping = {}
    for entry in registry.get("files", []):
        name = entry.get("name", "")
        rel_path = entry.get("path", "")
        if name and rel_path:
            abs_path = str((root / rel_path).resolve())
            mapping[abs_path] = name
    return mapping


def _trace_fn(frame, event, arg):
    """sys.settrace callback — fires on call/return/exception."""
    if not _trace_active:
        return None

    # Only trace call and return events
    if event not in ("call", "return", "exception"):
        return _trace_fn

    filename = frame.f_code.co_filename
    if not filename:
        return _trace_fn

    # Resolve to absolute path
    try:
        abs_path = os.path.abspath(filename)
    except Exception:
        return _trace_fn

    # Check if this file is a known pigeon module
    from_module = _module_map.get(abs_path)
    if not from_module:
        return _trace_fn

    # For calls, find what's being called (the caller's caller)
    to_module = None
    caller = frame.f_back
    if caller and caller.f_code.co_filename:
        try:
            caller_path = os.path.abspath(caller.f_code.co_filename)
            to_module = _module_map.get(caller_path)
        except Exception:
            pass

    global _seq_counter
    with _lock:
        _seq_counter += 1
        ev = {
            "seq": _seq_counter,
            "ts": int(time.time() * 1000),
            "event": event,
            "module": from_module,
            "func": frame.f_code.co_name,
            "caller": to_module,
            "line": frame.f_lineno,
        }
        if event == "exception" and arg:
            ev["error"] = str(arg[1])[:100] if len(arg) > 1 else str(arg[0])[:100]
        _event_buffer.append(ev)

    return _trace_fn
