"""钩w_th_s011_v002_d0323_缩分话_λP_buffer_ops_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 17 lines | ~130 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import os

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
