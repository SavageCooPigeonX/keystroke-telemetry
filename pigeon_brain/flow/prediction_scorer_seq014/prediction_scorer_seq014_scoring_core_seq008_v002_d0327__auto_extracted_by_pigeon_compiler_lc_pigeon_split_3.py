"""prediction_scorer_seq014_scoring_core_seq008_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 008 | VER: v002 | 69 lines | ~713 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: pigeon_split_3
# LAST:   2026-03-27 @ fd07906
# SESSIONS: 1
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from typing import Any
import re

def score_prediction(
    prediction: dict[str, Any],
    actual_modules: set[str],
    edit_pairs_in_window: list[dict[str, Any]],
    rework_signal: dict[str, Any],
) -> dict[str, Any]:
    """Score one prediction against edit-session reality + rework."""
    pred_result = prediction.get("result", {})
    pred_path = pred_result.get("path", [])
    pred_modules = set(pred_path)
    trend_modules = set(prediction.get("trend", {}).get("modules", []))
    pred_modules |= trend_modules

    if not pred_modules:
        return {**prediction, "score": {"f1": 0.0, "detail": "no_predicted_modules"}}

    hits = pred_modules & actual_modules
    misses = actual_modules - pred_modules
    false_pos = pred_modules - actual_modules

    precision = len(hits) / len(pred_modules) if pred_modules else 0.0
    recall = len(hits) / len(actual_modules) if actual_modules else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    # Outcome quality: did the edits in the window land well?
    rework_penalty = rework_signal.get("avg_rework", 0.0)
    miss_rate = rework_signal.get("miss_rate", 0.0)
    outcome_quality = max(0.0, 1.0 - rework_penalty - miss_rate * 0.5)

    # Combined score: module overlap + outcome quality
    combined = f1 * 0.6 + outcome_quality * 0.4

    # Confidence calibration error
    confidence = prediction.get("confidence", 0.5)
    calibration_error = abs(confidence - combined)

    return {
        "prediction_id": prediction.get("prediction_id", "?"),
        "batch_id": prediction.get("batch_id", "?"),
        "session_n_at": prediction.get("session_n_at", 0),
        "phantom_seed": prediction.get("phantom_seed", "")[:100],
        "mode": prediction.get("mode", "?"),
        "confidence": confidence,
        "ts_predicted": prediction.get("ts", ""),
        "ts_scored": datetime.now(timezone.utc).isoformat(),
        "score": {
            "precision": round(precision, 3),
            "recall": round(recall, 3),
            "f1": round(f1, 3),
            "outcome_quality": round(outcome_quality, 3),
            "combined": round(combined, 3),
            "calibration_error": round(calibration_error, 3),
            "rework_penalty": round(rework_penalty, 3),
            "hits": sorted(hits),
            "misses": sorted(misses)[:10],
            "false_positives": sorted(false_pos)[:10],
            "hit_count": len(hits),
            "miss_count": len(misses),
            "false_pos_count": len(false_pos),
            "edits_in_window": len(edit_pairs_in_window),
        },
        "predicted_path": pred_path[:10],
        "actual_modules": sorted(actual_modules)[:20],
    }
