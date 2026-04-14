"""合p_us_s026_v002_d0330_缩分话_λF_nearest_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 19 lines | ~172 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from typing import Any

def _find_nearest(entries: list[dict[str, Any]], target_ms: float,
                   ts_key: str = "ts", window_ms: float = JOIN_WINDOW_MS
                   ) -> dict[str, Any] | None:
    """Find the entry closest to target_ms within window."""
    best = None
    best_delta = window_ms
    for e in entries:
        e_ms = _parse_ts(e.get(ts_key, 0))
        delta = abs(e_ms - target_ms)
        if delta < best_delta:
            best_delta = delta
            best = e
    return best


JOIN_WINDOW_MS = 15_000  # 15s window for correlating events across sources
