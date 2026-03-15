"""streaming_layer_simulation_helpers_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 20 lines | ~141 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-03-15 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import time

def _sim_type(server, text, buf="", wpm=80):
    delay = 60.0 / (wpm * 5)
    for ch in text:
        buf += ch
        server.log_event("insert", ch, len(buf), buf)
        time.sleep(delay)
    return buf


def _sim_backspace(server, buf, count=1):
    for _ in range(count):
        if buf:
            removed = buf[-1]
            buf = buf[:-1]
            server.log_event("backspace", removed, len(buf), buf)
            time.sleep(0.03)
    return buf
