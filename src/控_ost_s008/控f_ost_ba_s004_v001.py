"""operator_stats_seq008_baselines_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def compute_baselines(history: list[dict], window: int = 50) -> dict:
    """Compute rolling baselines from operator history for self-calibration.

    Returns per-metric averages and std-dev approximations from the last
    `window` entries. These baselines let classify_state adapt to each
    operator's natural typing patterns instead of using hardcoded thresholds.
    """
    recent = [
        r for r in history[-window:]
        if r.get("submitted", True) and not _is_artifact_record(r)
    ]
    if len(recent) < 5:
        return {}  # not enough data to calibrate
    wpms = [r["wpm"] for r in recent if "wpm" in r and r["wpm"] <= WPM_HUMAN_MAX]
    dels = [r["del_ratio"] for r in recent if "del_ratio" in r]
    hess = [r["hesitation"] for r in recent if "hesitation" in r]
    if not wpms:
        return {}
    n = len(wpms)
    avg_wpm = sum(wpms) / n
    avg_del = sum(dels) / max(len(dels), 1)
    avg_hes = sum(hess) / max(len(hess), 1)
    # Simple std-dev (population)
    sd_wpm = (sum((w - avg_wpm) ** 2 for w in wpms) / n) ** 0.5
    sd_del = (sum((d - avg_del) ** 2 for d in dels) / max(len(dels), 1)) ** 0.5
    sd_hes = (sum((h - avg_hes) ** 2 for h in hess) / max(len(hess), 1)) ** 0.5
    return {
        "n": n,
        "avg_wpm": round(avg_wpm, 1),
        "avg_del": round(avg_del, 3),
        "avg_hes": round(avg_hes, 3),
        "sd_wpm": round(sd_wpm, 1),
        "sd_del": round(sd_del, 3),
        "sd_hes": round(sd_hes, 3),
    }
