"""streaming_layer_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 44 lines | ~199 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-03-15 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json

DEFAULT_PORT = 8787

MAX_CLIENTS = 50

EVENT_BUFFER_SIZE = 1000

SLIDING_WINDOW_MS = 30_000  # 30 seconds

ALERT_COOLDOWN_MS = 5_000

HEARTBEAT_INTERVAL_MS = 10_000

MAX_REPLAY_EVENTS = 10_000

PERCENTILE_TARGETS = [50, 75, 90, 95, 99]

CSV_SEPARATOR = ","

COMPACT_SEPARATOR = "|"


STREAM_FORMATS = {
    "json": "application/json",
    "csv": "text/csv",
    "compact": "text/plain",
    "sse": "text/event-stream",
}


ALERT_THRESHOLDS = {
    "pause_duration_ms": 5000,
    "deletion_burst_length": 10,
    "wpm_drop_percent": 50,
    "hesitation_score": 0.7,
    "discard_streak": 3,
}


DASHBOARD_REFRESH_MS = 500

AGGREGATION_INTERVALS = [5_000, 15_000, 30_000, 60_000]  # 5s, 15s, 30s, 60s
