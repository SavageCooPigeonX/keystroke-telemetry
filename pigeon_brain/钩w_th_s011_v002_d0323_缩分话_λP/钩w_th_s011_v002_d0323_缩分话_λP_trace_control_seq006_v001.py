"""钩w_th_s011_v002_d0323_缩分话_λP_trace_control_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 22 lines | ~152 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import sys
import threading

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
