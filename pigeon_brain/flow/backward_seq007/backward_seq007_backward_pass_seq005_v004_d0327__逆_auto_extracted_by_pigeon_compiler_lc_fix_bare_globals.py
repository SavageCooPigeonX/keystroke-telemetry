"""backward_seq007_backward_pass_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v004 | 101 lines | ~910 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: fix_bare_globals
# LAST:   2026-03-27 @ e894b6a
# SESSIONS: 3
# ──────────────────────────────────────────────
from pigeon_brain.flow._resolve import flow_import as _fi
append_learning = _fi("node_memory_seq008", "append_learning")
from pathlib import Path
from typing import Any
import re

def backward_pass(
    root: Path, electron_id: str,
    journal_entry: dict[str, Any], fix_context: str = "",
    use_deepseek: bool = True,
) -> list[dict[str, Any]]:
    """Run backward pass for a completed electron. Returns learning results.
    
    When use_deepseek=True, fires a DeepSeek call to produce rich contribution
    summaries and behavioral directives per node. Falls back to heuristic
    summaries if DeepSeek is unavailable.
    """
    forward = _load_forward_path(root, electron_id)
    if forward is None:
        return []

    path = forward.get("path", [])
    accumulated = forward.get("accumulated", [])
    task_seed = forward.get("task_seed", "")

    if not path or not accumulated:
        return []

    loss = compute_loss(journal_entry)
    fix_tokens = _tokenize(fix_context or journal_entry.get("msg", ""))
    signals = journal_entry.get("signals", {})
    state = journal_entry.get("cognitive_state", "unknown")
    del_ratio = signals.get("deletion_ratio", 0.0)
    intel_by_node = {i.get("node", ""): i for i in accumulated}

    # DeepSeek analysis for rich summaries
    ds_analyses: dict[str, dict] = {}
    ds_insight = ""
    if use_deepseek:
        analysis = _deepseek_analyze_backward(
            task_seed, path, accumulated, journal_entry, loss,
        )
        for na in analysis.get("node_analyses", []):
            ds_analyses[na.get("node", "")] = na
        ds_insight = analysis.get("system_insight", "")
        if ds_insight:
            logger.info(f"[backward] DeepSeek insight: {ds_insight}")

    results = []
    path_len = len(path)

    # Walk path in REVERSE
    for position, node_name in enumerate(reversed(path)):
        intel = intel_by_node.get(node_name)
        if intel is None:
            continue  # node was on path but didn't contribute (gated out)

        credit = _compute_credit(intel, position, path_len, fix_tokens)

        # Use DeepSeek summary if available, else heuristic
        ds_node = ds_analyses.get(node_name, {})
        if ds_node.get("summary"):
            summary = ds_node["summary"][:200]
        else:
            fears_str = ", ".join(intel.get("fears", [])[:2])
            summary = f"dual={intel.get('dual_score', 0):.2f}"
            if fears_str:
                summary += f"; fears: {fears_str}"

        record = append_learning(
            root=root,
            node=node_name,
            electron_id=electron_id,
            task_seed=task_seed,
            contribution_summary=summary,
            credit_score=credit,
            outcome_loss=loss,
            operator_state_after=state,
            rework_score=journal_entry.get("rework_score", 0.0),
            deletion_ratio_after=del_ratio,
        )
        results.append({
            "node": node_name, "credit": credit, "loss": loss,
            "deepseek_directive": ds_node.get("directive", ""),
            "failure_reason": ds_node.get("failure_reason", ""),
        })

    # Log system insight to flow log
    if ds_insight:
        _append_insight(root, electron_id, ds_insight, loss)

    return results
