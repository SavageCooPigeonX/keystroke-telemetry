"""learning_loop_seq013_prediction_cycle_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v003 | 37 lines | ~415 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: dynamic_import_resolvers
# LAST:   2026-03-28 @ b1971c0
# SESSIONS: 4
# ──────────────────────────────────────────────
from pathlib import Path
from typing import Any

def run_prediction_cycle(root: Path, state: dict[str, Any]) -> int:
    """Fire phantom electrons from cognitive profile."""
    from pigeon_brain.flow._resolve import flow_import
    predict_next_needs = flow_import("predictor_seq009", "predict_next_needs")
    run_flow = flow_import("flow_engine_seq003", "run_flow")
    # Score any existing predictions against edit sessions (primary)
    try:
        score_predictions_post_edit = flow_import(
            "prediction_scorer_seq014", "score_predictions_post_edit",
        )
        score_result = score_predictions_post_edit(root)
        if score_result.get("status") == "scored":
            logger.info(
                f"[loop] Scored {score_result['predictions_scored']} predictions "
                f"avg_combined={score_result['avg_combined']:.3f} "
                f"avg_f1={score_result['avg_f1']:.3f} "
                f"overconf={score_result['overconfidence_rate']:.2f} "
                f"nodes_updated={score_result['nodes_updated']}"
            )
    except Exception as e:
        logger.warning(f"[loop] Prediction scoring failed: {e}")

    predictions = predict_next_needs(root, run_flow_fn=run_flow)
    state["total_predictions"] += len(predictions)
    return len(predictions)
