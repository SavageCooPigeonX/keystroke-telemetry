"""operator_stats_classify_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
import time as _time

def classify_state(msg: dict) -> str:
    """Classify a finalized message dict into a cognitive state label."""
    keys = max(msg.get("total_keystrokes", 0), 1)
    inserts = msg.get("total_inserts", 0)
    dels = msg.get("total_deletions", 0)
    pauses = msg.get("typing_pauses", [])
    duration_ms = max(msg.get("end_time_ms", 0) - msg.get("start_time_ms", 0), 1)
    hes = msg.get("hesitation_score", 0)

    del_ratio = dels / keys
    wpm = (inserts / 5) / max(duration_ms / 60_000, 0.001)
    pause_ratio = sum(p.get("duration_ms", 0) for p in pauses) / duration_ms

    if msg.get("deleted"):
        return "abandoned"
    if hes > 0.6 or (del_ratio > 0.3 and pause_ratio > 0.3):
        return "frustrated"
    if pause_ratio > 0.4 or hes > 0.4:
        return "hesitant"
    if wpm > 60 and del_ratio < 0.05 and hes < 0.15:
        return "flow"
    if wpm > 40 and hes < 0.25:
        return "focused"
    if del_ratio > 0.20:
        return "restructuring"
    return "neutral"
