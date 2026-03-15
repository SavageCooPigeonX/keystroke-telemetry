"""streaming_layer_metrics_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v001 | 82 lines | ~723 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-03-15 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import deque
import math
import statistics

class MetricsCollector:
    """Collects and computes percentile metrics from event stream."""

    def __init__(self):
        self._delta_samples: deque = deque(maxlen=5000)
        self._wpm_samples: deque = deque(maxlen=500)
        self._hesitation_samples: deque = deque(maxlen=200)
        self._session_durations: list[int] = []
        self._total_events = 0
        self._total_submits = 0
        self._total_discards = 0

    def record_event(self, event: dict):
        self._total_events += 1
        delta = event.get("delta_ms", 0)
        if delta > 0:
            self._delta_samples.append(delta)

        etype = event.get("event_type", "")
        if etype == "submit":
            self._total_submits += 1
        elif etype in ("clear", "discard"):
            self._total_discards += 1

    def record_wpm(self, wpm: float):
        if wpm > 0:
            self._wpm_samples.append(wpm)

    def record_hesitation(self, score: float):
        self._hesitation_samples.append(score)

    def record_session_duration(self, duration_ms: int):
        self._session_durations.append(duration_ms)

    def _percentiles(self, data: list, targets: list[int] = None) -> dict:
        targets = targets or PERCENTILE_TARGETS
        if not data:
            return {f"p{t}": 0 for t in targets}
        sorted_data = sorted(data)
        result = {}
        for t in targets:
            idx = int(math.ceil(len(sorted_data) * t / 100)) - 1
            idx = max(0, min(idx, len(sorted_data) - 1))
            result[f"p{t}"] = sorted_data[idx]
        return result

    def get_delta_percentiles(self) -> dict:
        return self._percentiles(list(self._delta_samples))

    def get_wpm_percentiles(self) -> dict:
        return self._percentiles(list(self._wpm_samples))

    def get_summary(self) -> dict:
        delta_p = self.get_delta_percentiles()
        wpm_p = self.get_wpm_percentiles()

        avg_hes = 0.0
        if self._hesitation_samples:
            avg_hes = round(statistics.mean(self._hesitation_samples), 3)

        return {
            "total_events": self._total_events,
            "total_submits": self._total_submits,
            "total_discards": self._total_discards,
            "submit_rate": round(
                self._total_submits / max(self._total_submits + self._total_discards, 1), 3
            ),
            "delta_percentiles": delta_p,
            "wpm_percentiles": wpm_p,
            "avg_hesitation": avg_hes,
            "sample_counts": {
                "delta": len(self._delta_samples),
                "wpm": len(self._wpm_samples),
                "hesitation": len(self._hesitation_samples),
                "sessions": len(self._session_durations),
            },
        }
