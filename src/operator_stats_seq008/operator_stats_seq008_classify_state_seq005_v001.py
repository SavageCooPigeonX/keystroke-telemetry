"""operator_stats_seq008_classify_state_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
import re
import time as _time

def classify_state(msg: dict, baselines: dict | None = None) -> str:
    """Classify a finalized message dict into a cognitive state label.

    If baselines are provided (from compute_baselines), thresholds adapt
    to the operator's personal norms. Otherwise falls back to defaults.
    """
    keys = max(msg.get("total_keystrokes", 0), 1)
    inserts = msg.get("total_inserts", 0)
    dels = msg.get("total_deletions", 0)
    pauses = msg.get("typing_pauses", [])
    duration_ms = max(
        msg.get("effective_duration_ms",
                msg.get("end_time_ms", 0) - msg.get("start_time_ms", 0)),
        1,
    )
    hes = msg.get("hesitation_score", 0)

    del_ratio = dels / keys
    wpm = (inserts / 5) / max(duration_ms / 60_000, 0.001)
    pause_ratio = sum(p.get("duration_ms", 0) for p in pauses) / duration_ms

    if msg.get("deleted"):
        return "abandoned"

    # Adaptive thresholds: use operator baselines if available (5+ samples)
    if baselines and baselines.get("n", 0) >= 5:
        avg_wpm = baselines["avg_wpm"]
        avg_del = baselines["avg_del"]
        avg_hes = baselines["avg_hes"]
        sd_wpm = max(baselines["sd_wpm"], 1.0)
        sd_del = max(baselines["sd_del"], 0.01)
        sd_hes = max(baselines["sd_hes"], 0.01)

        # z-scores relative to operator's own norms
        z_wpm = (wpm - avg_wpm) / sd_wpm
        z_del = (del_ratio - avg_del) / sd_del
        z_hes = (hes - avg_hes) / sd_hes

        # frustrated: significantly more hesitation/deletion than their norm
        if z_hes > 1.2 or (z_del > 1.0 and pause_ratio > 0.25):
            return "frustrated"
        # hesitant: above-normal pausing/hesitation
        if z_hes > 0.8 or pause_ratio > 0.35:
            return "hesitant"
        # flow: significantly faster than their norm, low error
        if z_wpm > 0.8 and z_del < -0.5 and z_hes < -0.5:
            return "flow"
        # focused: above-average speed, below-average hesitation
        if z_wpm > 0.3 and z_hes < 0:
            return "focused"
        # restructuring: high deletion relative to their norm
        if z_del > 0.8:
            return "restructuring"
        return "neutral"

    # Fallback: hardcoded thresholds for cold-start (< 5 history entries)
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
