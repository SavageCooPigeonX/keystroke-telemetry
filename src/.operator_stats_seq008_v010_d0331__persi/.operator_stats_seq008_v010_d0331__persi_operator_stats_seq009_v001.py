""".operator_stats_seq008_v010_d0331__persi_operator_stats_seq009_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import re
import time as _time

class OperatorStats:
    """Accumulates operator cognitive stats and writes a markdown memory file.

    Usage:
        stats = OperatorStats("operator_profile.md")
        # called automatically by logger every finalize:
        stats.ingest(message_dict)
        # ^^ silently writes .md every `write_every` messages
    """

    def __init__(self, stats_path: str = "operator_profile.md", write_every: int = 8):
        self.stats_path = Path(stats_path)
        self.write_every = write_every
        self._msg_count = 0
        self._history: list[dict] = []
        self._load_existing()

    def _load_existing(self):
        """Bootstrap from existing stats file if present (read the JSON block)."""
        if not self.stats_path.exists():
            return
        text = self.stats_path.read_text(encoding="utf-8")
        m = re.search(r'<!--\s*\n?DATA\s*\n(.*?)\nDATA\s*\n-->', text, re.DOTALL)
        if not m:
            return
        try:
            data = json.loads(m.group(1).strip())
            self._history = data.get("history", [])
            self._msg_count = len(self._history)
        except (json.JSONDecodeError, TypeError):
            pass

    def ingest(self, msg: dict):
        """Ingest a finalized message dict. Writes .md every write_every messages."""
        baselines = compute_baselines(self._history)
        state = classify_state(msg, baselines)
        keys = max(msg.get("total_keystrokes", 0), 1)
        inserts = msg.get("total_inserts", 0)
        dels = msg.get("total_deletions", 0)
        duration_ms = max(
            msg.get("effective_duration_ms",
                msg.get("end_time_ms", 0) - msg.get("start_time_ms", 0)),
            1,
        )
        pauses = msg.get("typing_pauses", [])

        wpm = round((inserts / 5) / max(duration_ms / 60_000, 0.001), 1)
        # Prefer intent_deletion_ratio (8+ backspace runs only) over raw ratio
        del_ratio = msg.get('intent_deletion_ratio',
                           msg.get('chat_intent_deletion_ratio',
                                   round(dels / keys, 3)))
        pause_time_ms = sum(p.get("duration_ms", 0) for p in pauses)
        hes = msg.get("hesitation_score", 0)

        local_hour = _local_hour_now()
        record = {
            "state": state,
            "wpm": wpm,
            "del_ratio": del_ratio,
            "hesitation": hes,
            "pause_ms": pause_time_ms,
            "keys": msg.get("total_keystrokes", 0),
            "submitted": msg.get("submitted", False),
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "local_hour": local_hour,
            "slot": _hour_to_slot(local_hour),
        }
        self._history.append(record)
        self._msg_count += 1

        if self._msg_count % self.write_every == 0:
            self.flush()

    def flush(self):
        """Force-write the markdown stats file now."""
        if not self._history:
            return
        self.stats_path.write_text(_render_markdown(self._history, self.write_every), encoding="utf-8")
