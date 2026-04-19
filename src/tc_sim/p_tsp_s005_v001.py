"""tc_sim_seq001_v001_pause_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 57 lines | ~569 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from src.tc_constants_seq001_v001 import KEYSTROKE_LOG, DEFAULT_PAUSE_MS, ROOT
import os
import re
import time

def find_pause_points(session: TypingSession,
                      pause_ms: int = DEFAULT_PAUSE_MS,
                      min_buffer_len: int = 4) -> list[PausePoint]:
    """Find moments where the operator paused long enough to trigger completion.

    Returns pauses with the buffer state AT the pause and AFTER resumption.
    """
    pauses: list[PausePoint] = []
    events = session.events
    if len(events) < 3:
        return pauses

    for i in range(1, len(events) - 1):
        prev_ts = events[i - 1].get('ts', 0)
        curr_ts = events[i].get('ts', 0)
        gap = curr_ts - prev_ts

        if gap >= pause_ms:
            # Buffer at the pause = last event before the gap
            buf_at_pause = events[i - 1].get('buffer', '')
            if len(buf_at_pause) < min_buffer_len:
                continue

            # Buffer after resumption — scan ahead to find the NEXT stable point.
            # Use the buffer ~10 events later, or at the next pause/submit.
            # This gives us what they actually typed RIGHT AFTER this pause,
            # not what was ultimately submitted (which could be a total rewrite).
            lookahead = min(i + 15, len(events) - 1)
            buf_after = events[lookahead].get('buffer', '')
            # If the buffer shrunk (backspace cycle), use 5-event lookahead
            if len(buf_after) < len(buf_at_pause):
                buf_after = events[min(i + 5, len(events) - 1)].get('buffer', '')

            # Position in session timeline
            if session.duration_ms > 0:
                pos = (prev_ts - session.start_ts) / session.duration_ms
            else:
                pos = 0.5

            pauses.append(PausePoint(
                ts=prev_ts,
                buffer=buf_at_pause,
                pause_ms=gap,
                buffer_after=buf_after,
                final_text=session.final_buffer,
                position_pct=round(pos, 2),
            ))

    session.pause_points = [{'ts': p.ts, 'buffer': p.buffer[:60],
                             'pause_ms': p.pause_ms} for p in pauses]
    return pauses
