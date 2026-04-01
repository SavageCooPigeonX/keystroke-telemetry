""".operator_stats_seq008_v010_d0331__persi_baselines_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def compute_baselines(history: list[dict], window: int = 200) -> dict:
    """Compute rolling baselines from operator history for self-calibration.

    Uses ALL human-speed messages (submitted or not — discards carry valid
    cognitive signal) with exponential decay weighting (half-life 25 messages)
    so recent typing patterns dominate over stale data.
    """
    recent = [
        r for r in history[-window:]
        if not _is_artifact_record(r)
    ]
    if len(recent) < 5:
        return {}  # not enough data to calibrate

    n = len(recent)
    weights = [2.0 ** ((i - n + 1) / 25.0) for i in range(n)]

    wpm_pairs = [(r["wpm"], w) for r, w in zip(recent, weights)
                 if "wpm" in r and r["wpm"] <= WPM_HUMAN_MAX]
    del_pairs = [(r["del_ratio"], w) for r, w in zip(recent, weights)
                 if "del_ratio" in r]
    hes_pairs = [(r["hesitation"], w) for r, w in zip(recent, weights)
                 if "hesitation" in r]
    if not wpm_pairs:
        return {}

    def _wavg(pairs):
        tw = sum(w for _, w in pairs)
        return sum(v * w for v, w in pairs) / tw

    def _wsd(pairs, avg):
        tw = sum(w for _, w in pairs)
        return (sum(w * (v - avg) ** 2 for v, w in pairs) / tw) ** 0.5

    avg_wpm = _wavg(wpm_pairs)
    avg_del = _wavg(del_pairs) if del_pairs else 0
    avg_hes = _wavg(hes_pairs) if hes_pairs else 0
    sd_wpm = _wsd(wpm_pairs, avg_wpm)
    sd_del = _wsd(del_pairs, avg_del) if del_pairs else 0
    sd_hes = _wsd(hes_pairs, avg_hes) if hes_pairs else 0
    return {
        "n": len(wpm_pairs),
        "avg_wpm": round(avg_wpm, 1),
        "avg_del": round(avg_del, 3),
        "avg_hes": round(avg_hes, 3),
        "sd_wpm": round(sd_wpm, 1),
        "sd_del": round(sd_del, 3),
        "sd_hes": round(sd_hes, 3),
    }
