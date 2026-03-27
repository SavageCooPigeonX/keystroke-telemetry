"""prediction_scorer_seq014_post_edit_scorer_seq011_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 011 | VER: v002 | 89 lines | ~767 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: pigeon_split_3
# LAST:   2026-03-27 @ fd07906
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
from typing import Any
import json
import re

def score_predictions_post_edit(root: Path) -> dict[str, Any]:
    """Score predictions against edit sessions (primary scoring method).

    Uses edit_pairs.jsonl + rework_log.json as reality signals.
    Should be called frequently (every prediction cycle in the learning loop).
    """
    from .predictor_seq009_v003_d0327__fires_phantom_electrons_using_cognitive_lc_pigeon_split_3 import (
        load_predictions, save_predictions,
    )

    predictions = load_predictions(root)
    if not predictions:
        return {"status": "no_predictions", "scored": 0}

    edit_pairs = _load_edit_pairs(root)
    rework_entries = _load_rework_log(root)

    # Only score predictions that haven't been scored yet
    unscored = [p for p in predictions if not p.get("scored")]
    if not unscored:
        return {"status": "all_scored", "scored": 0}

    # Need enough subsequent data to evaluate
    max_session_n = max(
        (ep.get("session_n", 0) for ep in edit_pairs), default=0
    )

    scored_results = []
    newly_scored_ids = set()

    for pred in unscored:
        pred_sn = pred.get("session_n_at", 0)
        # Skip if we don't have enough subsequent edits yet
        if max_session_n < pred_sn + 2:
            continue

        actual_modules, matching_edits = _get_edit_session_modules(
            edit_pairs, pred_sn, EVAL_WINDOW,
        )
        if not actual_modules:
            continue

        journal_window = _load_journal_window(root, pred_sn, EVAL_WINDOW)
        rework_signal = _get_rework_in_window(rework_entries, journal_window)

        result = score_prediction(pred, actual_modules, matching_edits, rework_signal)
        scored_results.append(result)
        newly_scored_ids.add(pred.get("prediction_id"))

    if not scored_results:
        return {"status": "no_scorable", "scored": 0}

    # Mark predictions as scored
    for pred in predictions:
        if pred.get("prediction_id") in newly_scored_ids:
            pred["scored"] = True
    save_predictions(root, predictions)

    # Backfill into node memory
    nodes_updated = backfill_prediction_scores(root, scored_results)

    # Update calibration
    cal = _update_calibration(root, scored_results)

    # Persist scored results
    existing = _load_scores(root)
    existing.extend(scored_results)
    _save_scores(root, existing)

    combineds = [s["score"]["combined"] for s in scored_results]
    avg_combined = sum(combineds) / len(combineds) if combineds else 0.0

    return {
        "status": "scored",
        "predictions_scored": len(scored_results),
        "avg_combined": round(avg_combined, 3),
        "avg_f1": round(
            sum(s["score"]["f1"] for s in scored_results) / len(scored_results), 3
        ),
        "nodes_updated": nodes_updated,
        "overconfidence_rate": cal.get("overconfidence_rate", 0.0),
        "edits_available": len(edit_pairs),
    }
