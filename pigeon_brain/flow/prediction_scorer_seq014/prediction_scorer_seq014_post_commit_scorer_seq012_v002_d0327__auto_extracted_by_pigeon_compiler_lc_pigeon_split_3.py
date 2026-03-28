"""prediction_scorer_seq014_post_commit_scorer_seq012_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 012 | VER: v002 | 60 lines | ~542 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: pigeon_split_3
# LAST:   2026-03-27 @ fd07906
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
from typing import Any
import re
import subprocess

def score_predictions_post_commit(root: Path) -> dict[str, Any]:
    """Secondary audit: score against git diff HEAD~1 (delayed confirmation).

    Supplements edit-session scoring with commit-level ground truth.
    """
    from pigeon_brain.flow._resolve import flow_import
    load_predictions = flow_import("predictor_seq009", "load_predictions")

    predictions = load_predictions(root)
    if not predictions:
        return {"status": "no_predictions", "scored": 0}

    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            capture_output=True, text=True, cwd=str(root), timeout=10,
        )
        if result.returncode != 0:
            return {"status": "no_diff", "scored": 0}
        changed = [f.strip() for f in result.stdout.strip().splitlines() if f.strip()]
    except Exception:
        return {"status": "no_diff", "scored": 0}

    if not changed:
        return {"status": "no_diff", "scored": 0}

    actual_modules = {extract_module_name(f) for f in changed}
    actual_modules.discard(None)

    rework_entries = _load_rework_log(root)
    rework_signal = {"avg_rework": 0.0, "miss_rate": 0.0, "n_matched": 0}
    if rework_entries:
        scores = [r.get("rework_score", 0.0) for r in rework_entries[-10:]]
        rework_signal["avg_rework"] = sum(scores) / len(scores) if scores else 0.0

    scored = [score_prediction(p, actual_modules, [], rework_signal) for p in predictions]
    nodes_updated = backfill_prediction_scores(root, scored)

    existing = _load_scores(root)
    existing.extend(scored)
    _save_scores(root, existing)

    f1s = [s["score"]["f1"] for s in scored]
    avg_f1 = sum(f1s) / len(f1s) if f1s else 0.0

    return {
        "status": "scored",
        "predictions_scored": len(scored),
        "avg_f1": round(avg_f1, 3),
        "nodes_updated": nodes_updated,
        "changed_files": len(changed),
        "actual_modules": sorted(actual_modules)[:15],
    }
