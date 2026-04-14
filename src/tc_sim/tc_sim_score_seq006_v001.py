"""tc_sim_score_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 39 lines | ~381 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def score_prediction(pause: PausePoint, prediction: str) -> SimResult:
    """Score a prediction against what was actually typed.
    
    Uses buffer_after (what they typed immediately after this pause) as
    primary ground truth. Falls back to final_text only when buffer_after
    extends the buffer naturally (no rewrite detected).
    """
    # Primary: what they typed right after this pause
    local_cont = _extract_continuation(pause.buffer, pause.buffer_after)
    # Fallback: what was ultimately submitted
    final_cont = _extract_continuation(pause.buffer, pause.final_text)
    
    # Use local continuation if it exists and is different from final
    # (meaning the operator rewrote after this pause)
    if local_cont and local_cont != final_cont:
        continuation = local_cont  # rewrite detected — use local ground truth
    elif local_cont:
        continuation = local_cont
    else:
        continuation = final_cont
    
    result = SimResult(
        pause=pause,
        prediction=prediction,
        continuation_captured=continuation,
    )
    if not prediction or not continuation:
        return result

    pred_clean = prediction.strip().lower()
    cont_clean = continuation.strip().lower()

    result.exact_match = pred_clean == cont_clean
    result.prefix_match_len = _prefix_match(pred_clean, cont_clean)
    result.word_overlap = round(_word_overlap(pred_clean, cont_clean), 3)
    return result
