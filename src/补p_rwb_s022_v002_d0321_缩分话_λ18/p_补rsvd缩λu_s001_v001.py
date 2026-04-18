"""补p_rwb_s022_v002_d0321_缩分话_λ18_utils_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 19 lines | ~182 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone

def _ts_to_ms(ts_str: str) -> float:
    """Parse ISO-8601 ts to epoch ms. Returns 0.0 on failure."""
    try:
        dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        return dt.timestamp() * 1000
    except Exception:
        return 0.0


def _events_after(keystroke_events: list[dict], start_ms: float) -> list[dict]:
    """Return keystroke events in [start_ms, start_ms + REWORK_WINDOW_MS]."""
    end_ms = start_ms + REWORK_WINDOW_MS
    return [e for e in keystroke_events if start_ms <= e.get('ts', 0) <= end_ms]


REWORK_WINDOW_MS = 30_000   # 30s post-response window
