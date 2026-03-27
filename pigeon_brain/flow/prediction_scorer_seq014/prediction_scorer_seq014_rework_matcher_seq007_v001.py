"""prediction_scorer_seq014_rework_matcher_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from typing import Any
import re

def _get_rework_in_window(
    rework_entries: list[dict[str, Any]],
    journal_entries: list[dict[str, Any]],
) -> dict[str, Any]:
    """Match rework verdicts to journal entries in the window by timestamp.

    Returns aggregated rework signal.
    """
    if not rework_entries or not journal_entries:
        return {"avg_rework": 0.0, "miss_rate": 0.0, "n_matched": 0}

    # Build timestamp set from journal entries (±2s tolerance)
    journal_ts_ms = []
    for je in journal_entries:
        ts = je.get("ts", "")
        try:
            from datetime import datetime as _dt
            dt = _dt.fromisoformat(ts)
            journal_ts_ms.append(dt.timestamp() * 1000)
        except (ValueError, TypeError):
            continue

    matched_rework = []
    for rw in rework_entries:
        rw_ts = rw.get("ts", "")
        try:
            from datetime import datetime as _dt
            dt = _dt.fromisoformat(rw_ts)
            rw_ms = dt.timestamp() * 1000
        except (ValueError, TypeError):
            continue
        # Match if rework ts is within 60s of any journal entry in window
        for jts in journal_ts_ms:
            if abs(rw_ms - jts) < 60_000:
                matched_rework.append(rw)
                break

    if not matched_rework:
        return {"avg_rework": 0.0, "miss_rate": 0.0, "n_matched": 0}

    scores = [r.get("rework_score", 0.0) for r in matched_rework]
    misses = sum(1 for r in matched_rework if r.get("verdict") == "miss")
    return {
        "avg_rework": round(sum(scores) / len(scores), 3),
        "miss_rate": round(misses / len(matched_rework), 3),
        "n_matched": len(matched_rework),
    }
