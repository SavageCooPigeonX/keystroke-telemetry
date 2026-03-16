"""operator_stats_compute_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from datetime import datetime, timezone, timedelta
import time as _time

def _compute_record(msg, state, local_hour):
    """Extract and compute a compact record from a message dict."""
    keys = max(msg.get("total_keystrokes", 0), 1)
    inserts = msg.get("total_inserts", 0)
    dels = msg.get("total_deletions", 0)
    duration_ms = max(msg.get("end_time_ms", 0) - msg.get("start_time_ms", 0), 1)
    pauses = msg.get("typing_pauses", [])

    wpm = round((inserts / 5) / max(duration_ms / 60_000, 0.001), 1)
    del_ratio = round(dels / keys, 3)
    pause_time_ms = sum(p.get("duration_ms", 0) for p in pauses)
    hes = msg.get("hesitation_score", 0)

    return {
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
