"""streaming_layer_replay_seq009_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v002 | 108 lines | ~932 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: verify_pigeon_plugin
# LAST:   2026-03-15 @ caac48c
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
from typing import Optional, Callable
import json
import time

class SessionReplay:
    """Replays a session from JSONL file at real-time or accelerated speed."""

    def __init__(self, events_file: str):
        self.events_file = Path(events_file)
        self._events: list[dict] = []
        self._loaded = False

    def load(self):
        if not self.events_file.exists():
            raise FileNotFoundError(f"Events file not found: {self.events_file}")
        self._events = []
        with open(self.events_file, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i >= MAX_REPLAY_EVENTS:
                    break
                self._events.append(json.loads(line))
        self._loaded = True

    def event_count(self) -> int:
        return len(self._events)

    def duration_ms(self) -> int:
        if len(self._events) < 2:
            return 0
        return self._events[-1]["timestamp_ms"] - self._events[0]["timestamp_ms"]

    def replay(self, speed: float = 1.0, callback: Callable = None):
        """Replay events with timing. speed=2.0 means 2x faster."""
        if not self._loaded:
            self.load()

        if not self._events:
            return

        callback = callback or (lambda e: print(json.dumps(e, indent=2)))
        prev_ts = self._events[0]["timestamp_ms"]

        for event in self._events:
            ts = event["timestamp_ms"]
            gap_ms = ts - prev_ts
            if gap_ms > 0 and speed > 0:
                time.sleep((gap_ms / 1000) / speed)
            callback(event)
            prev_ts = ts

    def get_events(self, start: int = 0, count: int = 100) -> list[dict]:
        return self._events[start:start + count]

    def find_by_message(self, message_id: str) -> list[dict]:
        return [e for e in self._events if e.get("message_id") == message_id]

    def get_message_ids(self) -> list[str]:
        seen = []
        for e in self._events:
            mid = e.get("message_id")
            if mid and mid not in seen:
                seen.append(mid)
        return seen

    def summarize_messages(self) -> list[dict]:
        """Per-message summary from raw events."""
        messages = {}
        for e in self._events:
            mid = e.get("message_id", "unknown")
            if mid not in messages:
                messages[mid] = {
                    "message_id": mid,
                    "first_ts": e["timestamp_ms"],
                    "last_ts": e["timestamp_ms"],
                    "events": 0,
                    "inserts": 0,
                    "deletes": 0,
                    "pastes": 0,
                    "final_buffer": "",
                }
            m = messages[mid]
            m["events"] += 1
            m["last_ts"] = e["timestamp_ms"]
            m["final_buffer"] = e.get("buffer", "")
            etype = e.get("event_type", "")
            if etype == "insert":
                m["inserts"] += 1
            elif etype in ("delete", "backspace"):
                m["deletes"] += 1
            elif etype == "paste":
                m["pastes"] += 1

        for m in messages.values():
            m["duration_ms"] = m["last_ts"] - m["first_ts"]
            total = m["inserts"] + m["deletes"]
            m["deletion_ratio"] = round(m["deletes"] / max(total, 1), 3)

        return list(messages.values())
