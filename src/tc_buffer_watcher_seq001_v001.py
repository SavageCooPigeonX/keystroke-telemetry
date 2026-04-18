"""BufferWatcher — tails os_keystrokes.jsonl to read the live typing buffer."""
from __future__ import annotations
import json
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
        self._init_offset()

    def _init_offset(self):
        if self.log_path.exists():
            self._offset = self.log_path.stat().st_size

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
