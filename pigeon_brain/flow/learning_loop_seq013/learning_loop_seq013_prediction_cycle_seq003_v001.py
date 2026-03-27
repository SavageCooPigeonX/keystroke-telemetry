"""learning_loop_seq013_prediction_cycle_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from typing import Any

def run_prediction_cycle(root: Path, state: dict[str, Any]) -> int:
    """Fire phantom electrons from cognitive profile."""
    from .predictor_seq009_v002_d0327__fires_phantom_electrons_using_cognitive_lc_edit_session_prediction import (
        predict_next_needs,
    )
    from .flow_engine_seq003_v002_d0324__the_flow_engine_is_the_lc_flow_engine_context import (
        run_flow,
    )
    # Score any existing predictions against edit sessions (primary)
    try:
        from .prediction_scorer_seq014_v002_d0327__edit_session_based_lc_edit_session_prediction import (
            score_predictions_post_edit,
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
