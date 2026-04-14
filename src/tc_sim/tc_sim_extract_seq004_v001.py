"""tc_sim_extract_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 52 lines | ~482 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
from src.tc_constants import KEYSTROKE_LOG, DEFAULT_PAUSE_MS, ROOT
import json
import os
import re

def extract_sessions(log_path: Path = KEYSTROKE_LOG,
                     min_buffer_len: int = 8) -> list[TypingSession]:
    """Extract complete typing sessions from os_keystrokes.jsonl.

    A session = all events between buffer-empty and submit/discard.
    """
    sessions: list[TypingSession] = []
    current: list[dict] = []
    idx = 0

    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
            except (json.JSONDecodeError, ValueError):
                continue
            evt_type = evt.get('type', '')
            current.append(evt)

            if evt_type in ('submit', 'discard'):
                buf = evt.get('buffer', '')
                if len(buf) >= min_buffer_len:
                    sess = TypingSession(
                        index=idx,
                        events=current[:],
                        final_buffer=buf,
                        context=evt.get('context', 'editor'),
                        start_ts=current[0].get('ts', 0),
                        end_ts=evt.get('ts', 0),
                    )
                    sess.duration_ms = sess.end_ts - sess.start_ts
                    sess.keystroke_count = len(current)
                    sess.backspace_count = sum(
                        1 for e in current if e.get('type') == 'backspace'
                    )
                    idx += 1
                    sessions.append(sess)
                current = []
            elif evt_type == 'discard' or (evt_type == 'insert' and not current):
                current = [evt]

    return sessions
