"""BufferWatcher — tails os_keystrokes.jsonl to read the live typing buffer."""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations
import json
import time
from pathlib import Path


class BufferWatcher:
    """Tail os_keystrokes.jsonl to get the live typing buffer."""

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self._offset = 0
        self.buffer = ''
        self.context = 'editor'
        self.last_ts = 0
        self.last_event_type = ''
        self.hydrated_from_tail = False
        self._init_offset()

    def _init_offset(self):
        if self.log_path.exists():
            self._hydrate_from_tail()
            self._offset = self.log_path.stat().st_size

    def _hydrate_from_tail(self) -> None:
        """Seed the popup with the current live buffer on startup.

        Without this, launching the popup mid-composition starts tailing from
        EOF and only sees the words typed after launch, which makes pause sims
        look like they chopped off the beginning of the prompt.
        """
        try:
            size = self.log_path.stat().st_size
            if size <= 0:
                return
            with open(self.log_path, "rb") as handle:
                handle.seek(max(0, size - 65536))
                data = handle.read().decode("utf-8", errors="ignore")
            for line in reversed([part for part in data.splitlines() if part.strip()]):
                try:
                    evt = json.loads(line)
                except Exception:
                    continue
                evt_type = evt.get("type", "")
                evt_ts = evt.get("ts", 0)
                event_ms = float(evt_ts or 0)
                if 0 < event_ms < 10_000_000_000:
                    event_ms *= 1000
                if event_ms and (time.time() * 1000 - event_ms) > 10 * 60 * 1000:
                    return
                self.context = evt.get("context", self.context)
                self.last_ts = evt_ts
                self.last_event_type = evt_type
                if evt_type not in ("submit", "discard"):
                    self.buffer = evt.get("buffer", "") or ""
                    self.hydrated_from_tail = bool(self.buffer)
                return
        except Exception:
            return

    def poll(self) -> bool:
        """Read new lines from the log. Returns True if buffer changed."""
        if not self.log_path.exists():
            return False
        try:
            size = self.log_path.stat().st_size
            if size <= self._offset:
                if size < self._offset:
                    self._offset = 0  # file was truncated
                return False

            with open(self.log_path, 'rb') as f:
                f.seek(self._offset)
                new_data = f.read().decode('utf-8', errors='ignore')
                self._offset = f.tell()

            changed = False
            for line in new_data.strip().splitlines():
                try:
                    evt = json.loads(line)
                except Exception:
                    continue
                new_buf = evt.get('buffer', '')
                new_ctx = evt.get('context', self.context)
                new_ts = evt.get('ts', 0)
                evt_type = evt.get('type', '')
                if new_buf != self.buffer or new_ctx != self.context:
                    changed = True
                if evt_type in ('undo', 'submit', 'discard'):
                    changed = True
                self.buffer = new_buf
                self.context = new_ctx
                self.last_ts = new_ts
                self.last_event_type = evt_type
                if evt_type in ('submit', 'discard'):
                    self.buffer = ''
                    changed = True
            return changed
        except Exception:
            return False
