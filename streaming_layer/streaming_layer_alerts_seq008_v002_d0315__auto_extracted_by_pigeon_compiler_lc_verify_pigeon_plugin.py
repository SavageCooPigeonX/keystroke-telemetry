"""streaming_layer_alerts_seq008_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 008 | VER: v002 | 130 lines | ~1,280 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: verify_pigeon_plugin
# LAST:   2026-03-15 @ caac48c
# SESSIONS: 1
# ──────────────────────────────────────────────
from collections import deque
from dataclasses import dataclass, field, asdict
from typing import Optional, Callable
import statistics
import time
import uuid

from src._resolve import src_import
from streaming_layer._resolve import sl_import

_now_ms = src_import("timestamp_utils_seq001", "_now_ms")
ALERT_THRESHOLDS = sl_import("streaming_layer_constants_seq001", "ALERT_THRESHOLDS")
ALERT_COOLDOWN_MS = sl_import("streaming_layer_constants_seq001", "ALERT_COOLDOWN_MS")
Alert = sl_import("streaming_layer_dataclasses_seq006", "Alert")
EventAggregator = sl_import("streaming_layer_aggregator_seq006", "EventAggregator")


class AlertEngine:
    """Detects anomalies in the event stream and fires alerts."""

    def __init__(self, thresholds: dict = None):
        self.thresholds = thresholds or dict(ALERT_THRESHOLDS)
        self._alerts: list[Alert] = []
        self._last_alert_time: dict[str, int] = {}
        self._consecutive_deletes = 0
        self._consecutive_discards = 0
        self._baseline_wpm: Optional[float] = None
        self._wpm_history: deque = deque(maxlen=20)

    def process_event(self, event: dict, aggregator: EventAggregator) -> Optional[Alert]:
        now = event.get("timestamp_ms", _now_ms())
        etype = event.get("event_type", "")
        delta = event.get("delta_ms", 0)

        # Check: long pause
        if delta > self.thresholds["pause_duration_ms"]:
            return self._fire_alert(
                "long_pause", "warning",
                f"Long pause detected: {delta}ms",
                now, {"delta_ms": delta}
            )

        # Check: deletion burst
        if etype in ("delete", "backspace"):
            self._consecutive_deletes += 1
            if self._consecutive_deletes >= self.thresholds["deletion_burst_length"]:
                alert = self._fire_alert(
                    "deletion_burst", "warning",
                    f"Deletion burst: {self._consecutive_deletes} consecutive deletes",
                    now, {"count": self._consecutive_deletes}
                )
                self._consecutive_deletes = 0
                return alert
        else:
            self._consecutive_deletes = 0

        # Check: WPM drop
        current_wpm = aggregator.compute_rolling_wpm(5000)
        if current_wpm > 0:
            self._wpm_history.append(current_wpm)
            if self._baseline_wpm is None and len(self._wpm_history) >= 5:
                self._baseline_wpm = statistics.median(list(self._wpm_history))
            elif self._baseline_wpm and self._baseline_wpm > 0:
                drop_pct = ((self._baseline_wpm - current_wpm) / self._baseline_wpm) * 100
                if drop_pct > self.thresholds["wpm_drop_percent"]:
                    return self._fire_alert(
                        "wpm_drop", "info",
                        f"WPM dropped {drop_pct:.0f}%: {self._baseline_wpm:.0f} → {current_wpm:.0f}",
                        now, {"baseline": self._baseline_wpm, "current": current_wpm}
                    )

        # Check: discard streak
        if etype in ("clear", "discard"):
            self._consecutive_discards += 1
            if self._consecutive_discards >= self.thresholds["discard_streak"]:
                alert = self._fire_alert(
                    "discard_streak", "critical",
                    f"Discard streak: {self._consecutive_discards} messages abandoned",
                    now, {"count": self._consecutive_discards}
                )
                return alert
        elif etype == "submit":
            self._consecutive_discards = 0

        return None

    def process_hesitation(self, score: float) -> Optional[Alert]:
        if score > self.thresholds["hesitation_score"]:
            return self._fire_alert(
                "high_hesitation", "warning",
                f"High hesitation score: {score}",
                _now_ms(), {"score": score}
            )
        return None

    def _fire_alert(self, alert_type: str, severity: str, message: str,
                    timestamp_ms: int, context: dict) -> Optional[Alert]:
        # cooldown check
        last = self._last_alert_time.get(alert_type, 0)
        if timestamp_ms - last < ALERT_COOLDOWN_MS:
            return None

        alert = Alert(
            alert_id=uuid.uuid4().hex[:8],
            alert_type=alert_type,
            severity=severity,
            message=message,
            timestamp_ms=timestamp_ms,
            context=context,
        )
        self._alerts.append(alert)
        self._last_alert_time[alert_type] = timestamp_ms
        return alert

    def get_alerts(self, limit: int = 50) -> list[dict]:
        return [asdict(a) for a in self._alerts[-limit:]]

    def unacknowledged_count(self) -> int:
        return sum(1 for a in self._alerts if not a.acknowledged)

    def acknowledge(self, alert_id: str) -> bool:
        for a in self._alerts:
            if a.alert_id == alert_id:
                a.acknowledged = True
                return True
        return False

    def clear_alerts(self):
        self._alerts.clear()
        self._last_alert_time.clear()
