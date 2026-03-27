"""prediction_scorer_seq014_node_backfill_seq010_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 010 | VER: v004 | 53 lines | ~499 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: fix_bare_globals
# LAST:   2026-03-27 @ e894b6a
# SESSIONS: 3
# ──────────────────────────────────────────────
from pathlib import Path
from typing import Any
import hashlib
import re

def backfill_prediction_scores(root: Path, scored: list[dict[str, Any]]) -> int:
    """Feed prediction accuracy into node_memory with calibration-weighted penalties."""
    from pigeon_brain.flow._resolve import flow_import
    append_learning = flow_import("node_memory_seq008", "append_learning")

    updated = 0
    for s in scored:
        score_data = s.get("score", {})
        hits = score_data.get("hits", [])
        false_pos = score_data.get("false_positives", [])
        combined = score_data.get("combined", 0.0)
        cal_err = score_data.get("calibration_error", 0.0)
        seed = s.get("phantom_seed", "")[:80]
        eid = s.get("prediction_id", hashlib.md5(
            f"pred_{seed}_{s.get('ts_scored','')}".encode()).hexdigest()[:12])

        for node in hits:
            append_learning(
                root, node, eid,
                task_seed=seed,
                contribution_summary=f"pred_hit combined={combined:.2f}",
                credit_score=0.5 + combined * 0.4,
                outcome_loss=max(0.0, 0.3 - combined * 0.3),
            )
            updated += 1

        # Penalty scales with calibration error
        penalty_loss = min(0.7, 0.3 + cal_err * 0.4)
        for node in false_pos[:5]:
            append_learning(
                root, node, eid,
                task_seed=seed,
                contribution_summary=f"pred_false_pos cal_err={cal_err:.2f}",
                credit_score=0.15,
                outcome_loss=penalty_loss,
            )
            updated += 1

    return updated
