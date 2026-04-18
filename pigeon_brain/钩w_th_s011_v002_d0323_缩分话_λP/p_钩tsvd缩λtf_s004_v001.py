"""钩w_th_s011_v002_d0323_缩分话_λP_trace_fn_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 56 lines | ~403 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import os
import sys
import time

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
