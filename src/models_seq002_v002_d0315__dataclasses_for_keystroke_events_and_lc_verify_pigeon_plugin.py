# @pigeon: seq=002 | role=datamodels | depends=[timestamp_utils] | exports=[KeyEvent,MessageDraft] | tokens=~400
"""Dataclasses for keystroke events and message draft tracking."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v002 | 39 lines | ~351 tokens
# DESC:   dataclasses_for_keystroke_events_and
# INTENT: verify_pigeon_plugin
# LAST:   2026-03-15 @ caac48c
# SESSIONS: 1
# ──────────────────────────────────────────────

from dataclasses import dataclass, field


@dataclass
class KeyEvent:
    timestamp_ms: int        # epoch milliseconds
    event_type: str          # insert, delete, backspace, paste, cut, clear, undo, redo, submit
    key: str                 # the character or key name
    cursor_pos: int          # cursor position at time of event
    buffer_snapshot: str     # text buffer after event
    message_id: str          # groups events into one composition session
    delta_ms: int = 0        # ms since last event


@dataclass
class MessageDraft:
    message_id: str
    drafts: list = field(default_factory=list)
    final_text: str = ""
    submitted: bool = False
    deleted: bool = False
    total_keystrokes: int = 0
    total_deletions: int = 0
    total_inserts: int = 0
    start_time_ms: int = 0
    end_time_ms: int = 0
    typing_pauses: list = field(default_factory=list)
    hesitation_score: float = 0.0   # computed on finalize: pauses + deletion_ratio
