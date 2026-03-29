"""push_cycle_seq025_moon_cycle_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
import json

def _score_old_predictions(root: Path) -> dict:
    """Score predictions from the LAST push cycle against what actually happened."""
    try:
        scorer = _load_pigeon_module(root, 'pigeon_brain/flow', 'prediction_scorer_seq014*')
        if scorer and hasattr(scorer, 'score_predictions_post_commit'):
            return scorer.score_predictions_post_commit(root)
    except Exception as e:
        return {"status": "error", "error": str(e)[:200]}
    return {"status": "no_scorer"}


def _run_backward_on_entries(root: Path, entries: list[dict]) -> list[dict]:
    """Run backward pass on journal entries — distribute credit to nodes.

    Only runs on high-signal entries (frustrated/hesitant state or high deletion)
    to keep DeepSeek costs bounded. Max 3 backward passes per push.
    """
    backward_mod = _load_pigeon_module(root, 'pigeon_brain/flow', 'backward_seq007*')
    if not backward_mod or not hasattr(backward_mod, 'backward_pass'):
        return []

    # Select high-signal entries worth running backward pass on
    candidates = []
    for e in entries:
        signals = e.get("signals", {})
        state = e.get("cognitive_state", "unknown")
        del_ratio = signals.get("deletion_ratio", 0) or e.get("deletion_ratio", 0)
        if state in ("frustrated", "hesitant", "confused") or del_ratio > 0.3:
            candidates.append(e)

    # Cap at 3 to keep DeepSeek costs bounded (~$0.009 max per push)
    candidates = candidates[:3]
    results = []
    for entry in candidates:
        try:
            # Build a synthetic electron_id from the entry
            eid = entry.get("session_id", "") + "_" + str(entry.get("session_n", 0))
            backward_results = backward_mod.backward_pass(
                root,
                electron_id=eid,
                journal_entry=entry,
                fix_context=entry.get("msg", ""),
                use_deepseek=True,
            )
            results.extend(backward_results)
        except Exception:
            pass  # DeepSeek timeout or model error — skip, don't block push
    return results


def _fire_predictions(root: Path) -> list[dict]:
    """Fire new predictions for what operator will want next push cycle."""
    predictor = _load_pigeon_module(root, 'pigeon_brain/flow', 'predictor_seq009*')
    if not predictor or not hasattr(predictor, 'predict_next_needs'):
        return []

    try:
        predictions = predictor.predict_next_needs(
            root,
            run_flow_fn=None,  # no phantom execution — just predict
            n_predictions=3,
        )
        # Persist to prediction log for post-commit scoring
        log_path = root / PREDICTION_LOG_PATH
        log_path.parent.mkdir(parents=True, exist_ok=True)
        for p in predictions:
            p["cycle_ts"] = datetime.now(timezone.utc).isoformat()
        with open(log_path, "a", encoding="utf-8") as f:
            for p in predictions:
                f.write(json.dumps(p) + "\n")
        return predictions
    except Exception:
        return []
