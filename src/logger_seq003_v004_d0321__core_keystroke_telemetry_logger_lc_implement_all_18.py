# @pigeon: seq=003 | role=core_logger | depends=[timestamp_utils,models] | exports=[TelemetryLogger] | tokens=~1800 | coupling=0.7
"""Core keystroke telemetry logger.

Captures per-keystroke events within an app's text input for
cognitive-sync analytics: typos, deletions, rewrites, pauses.
Each event is emitted as a self-contained LLM-compatible JSON block
(schema: keystroke_telemetry/v2).
"""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v004 | 163 lines | ~1,540 tokens
# DESC:   core_keystroke_telemetry_logger
# INTENT: implement_all_18
# LAST:   2026-03-21 @ 068687f
# SESSIONS: 1
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# ── /pulse ──

import json
import uuid
from pathlib import Path
from dataclasses import asdict
from typing import Optional

_now_ms
from src = _load_src('timestamp_utils_seq001*.py', '_now_ms\nfrom src').models_seq002_v003_d0317__dataclasses_for_keystroke_events_and_lc_pulse_telemetry_prompt import KeyEvent, MessageDraft

def _load_src(pattern: str, *symbols):
    """Dynamic pigeon import — finds latest src/ file matching glob."""
    import importlib.util as _ilu, glob as _g
    matches = sorted(_g.glob(f'src/{pattern}'))
    if not matches:
        raise ImportError(f'No src/ file matches {pattern!r}')
    spec = _ilu.spec_from_file_location('_dyn', matches[-1])
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if len(symbols) == 1:
        return getattr(mod, symbols[0])
    return tuple(getattr(mod, s) for s in symbols)

OperatorStats

SCHEMA_VERSION = _load_src('operator_stats_seq008*.py', 'OperatorStats\n\nSCHEMA_VERSION')= "keystroke_telemetry/v2"


class TelemetryLogger:
    PAUSE_THRESHOLD_MS = 2000

    def __init__(self, log_dir: str = "logs", live_print: bool = True,
                 stats_path: str = "operator_profile.md", stats_every: int = 8):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.live_print = live_print

        self.session_id = uuid.uuid4().hex[:12]
        self.events_file = self.log_dir / f"events_{self.session_id}.jsonl"
        self.summary_file = self.log_dir / f"summary_{self.session_id}.json"

        self.current_message_id: Optional[str] = None
        self.current_draft: Optional[MessageDraft] = None
        self.last_event_time_ms: int = 0
        self.all_summaries: list = []
        self._event_seq = 0
        self._consecutive_deletes = 0

        self._events_handle = open(self.events_file, "a", encoding="utf-8")
        self._operator_stats = OperatorStats(stats_path, write_every=stats_every)

    def start_message(self) -> str:
        if self.current_draft and not self.current_draft.submitted and not self.current_draft.deleted:
            self._finalize_draft(deleted=True)

        self.current_message_id = uuid.uuid4().hex[:10]
        self.current_draft = MessageDraft(
            message_id=self.current_message_id,
            start_time_ms=_now_ms(),
        )
        self.last_event_time_ms = _now_ms()
        self._consecutive_deletes = 0
        return self.current_message_id

    def log_event(self, event_type: str, key: str, cursor_pos: int, buffer_text: str):
        now = _now_ms()
        delta = now - self.last_event_time_ms if self.last_event_time_ms else 0

        if self.current_message_id is None:
            self.start_message()

        self._event_seq += 1

        block = {
            "schema": SCHEMA_VERSION,
            "seq": self._event_seq,
            "session_id": self.session_id,
            "message_id": self.current_message_id,
            "timestamp_ms": now,
            "delta_ms": delta,
            "event_type": event_type,
            "key": key,
            "cursor_pos": cursor_pos,
            "buffer": buffer_text,
            "buffer_len": len(buffer_text),
        }

        self._events_handle.write(json.dumps(block) + "\n")
        self._events_handle.flush()

        if self.live_print:
            print(json.dumps(block, indent=2))

        draft = self.current_draft
        draft.total_keystrokes += 1

        if event_type in ("delete", "backspace"):
            draft.total_deletions += 1
            self._consecutive_deletes += 1
        else:
            if event_type == "insert":
                draft.total_inserts += 1
            # snapshot on deletion burst end (3+ consecutive deletes followed by non-delete)
            if self._consecutive_deletes >= 3:
                draft.drafts.append({"time_ms": now, "text": buffer_text, "trigger": "deletion_burst"})
            self._consecutive_deletes = 0

        if delta > self.PAUSE_THRESHOLD_MS:
            draft.typing_pauses.append({"at_ms": now, "duration_ms": delta})

        self.last_event_time_ms = now

    def submit_message(self, final_text: str):
        if self.current_draft:
            self._finalize_draft(submitted=True, final_text=final_text)

    def discard_message(self, buffer_text: str):
        if self.current_draft:
            self.current_draft.drafts.append({"time_ms": _now_ms(), "text": buffer_text, "trigger": "discard"})
            self._finalize_draft(deleted=True, final_text=buffer_text)

    def close(self):
        if self.current_draft and not self.current_draft.submitted:
            self._finalize_draft(deleted=True)
        self._write_summary()
        self._operator_stats.flush()
        self._events_handle.close()

    def _finalize_draft(self, submitted=False, deleted=False, final_text=""):
        d = self.current_draft
        d.submitted = submitted
        d.deleted = deleted
        d.final_text = final_text
        d.end_time_ms = _now_ms()

        # hesitation score: combination of pause frequency and deletion ratio
        duration = max(d.end_time_ms - d.start_time_ms, 1)
        pause_ratio = sum(p["duration_ms"] for p in d.typing_pauses) / duration
        deletion_ratio = d.total_deletions / max(d.total_keystrokes, 1)
        d.hesitation_score = round(min(pause_ratio + deletion_ratio, 1.0), 3)

        self.all_summaries.append(asdict(d))
        self._write_summary()
        self._operator_stats.ingest(self.all_summaries[-1])
        self.current_message_id = None
        self.current_draft = None

    def _write_summary(self):
        with open(self.summary_file, "w", encoding="utf-8") as f:
            json.dump({
                "schema": SCHEMA_VERSION,
                "session_id": self.session_id,
                "messages": self.all_summaries,
            }, f, indent=2)

# pigeon test marker
