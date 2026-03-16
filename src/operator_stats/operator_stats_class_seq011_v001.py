"""operator_stats_class_seq011_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json

class OperatorStats:
    def __init__(self, stats_path: str = "operator_profile.md", write_every: int = 8):
        self.stats_path = Path(stats_path)
        self.write_every = write_every
        self._msg_count = 0
        self._history: list[dict] = []
        self._load_existing()

    def _load_existing(self):
        if not self.stats_path.exists():
            return
        text = self.stats_path.read_text(encoding="utf-8")
        start = text.find("<!-- DATA")
        end = text.find("DATA -->")
        if start == -1 or end == -1:
            return
        json_str = text[start + len("<!-- DATA"):end].strip()
        try:
            data = json.loads(json_str)
            self._history = data.get("history", [])
            self._msg_count = len(self._history)
        except (json.JSONDecodeError, TypeError):
            pass

    def ingest(self, msg: dict):
        state = classify_state(msg)
        local_hour = _local_hour_now()
        record = _compute_record(msg, state, local_hour)
        self._history.append(record)
        self._msg_count += 1

        if self._msg_count % self.write_every == 0:
            self.flush()

    def flush(self):
        if not self._history:
            return
        self.stats_path.write_text(_render_full_markdown(self._history, self.write_every), encoding="utf-8")
