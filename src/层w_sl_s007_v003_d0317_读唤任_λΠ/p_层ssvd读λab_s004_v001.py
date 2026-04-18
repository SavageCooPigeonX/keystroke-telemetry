"""层w_sl_s007_v003_d0317_读唤任_λΠ_aggregation_bucket_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 76 lines | ~662 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from dataclasses import dataclass, field, asdict

@dataclass
class AggregationBucket:
    window_ms: int
    start_ms: int
    events: list = field(default_factory=list)
    insert_count: int = 0
    delete_count: int = 0
    paste_count: int = 0
    total_delta_ms: int = 0
    pause_count: int = 0
    max_delta_ms: int = 0
    min_delta_ms: int = 999999
    submit_count: int = 0
    discard_count: int = 0

    def add_event(self, event: dict):
        self.events.append(event)
        etype = event.get("event_type", "")
        delta = event.get("delta_ms", 0)

        if etype == "insert":
            self.insert_count += 1
        elif etype in ("delete", "backspace"):
            self.delete_count += 1
        elif etype == "paste":
            self.paste_count += 1
        elif etype == "submit":
            self.submit_count += 1
        elif etype in ("clear", "discard"):
            self.discard_count += 1

        self.total_delta_ms += delta
        if delta > self.max_delta_ms:
            self.max_delta_ms = delta
        if delta < self.min_delta_ms and delta > 0:
            self.min_delta_ms = delta
        if delta > 2000:
            self.pause_count += 1

    def avg_delta_ms(self) -> float:
        if not self.events:
            return 0.0
        return self.total_delta_ms / len(self.events)

    def estimated_wpm(self) -> float:
        if self.insert_count == 0 or self.total_delta_ms == 0:
            return 0.0
        chars_per_ms = self.insert_count / self.total_delta_ms
        return round(chars_per_ms * 60_000 / 5, 1)  # words = chars / 5

    def deletion_ratio(self) -> float:
        total = self.insert_count + self.delete_count
        if total == 0:
            return 0.0
        return round(self.delete_count / total, 3)

    def to_dict(self) -> dict:
        return {
            "window_ms": self.window_ms,
            "start_ms": self.start_ms,
            "event_count": len(self.events),
            "insert_count": self.insert_count,
            "delete_count": self.delete_count,
            "paste_count": self.paste_count,
            "submit_count": self.submit_count,
            "discard_count": self.discard_count,
            "pause_count": self.pause_count,
            "avg_delta_ms": round(self.avg_delta_ms(), 1),
            "max_delta_ms": self.max_delta_ms,
            "min_delta_ms": self.min_delta_ms if self.min_delta_ms < 999999 else 0,
            "estimated_wpm": self.estimated_wpm(),
            "deletion_ratio": self.deletion_ratio(),
        }
