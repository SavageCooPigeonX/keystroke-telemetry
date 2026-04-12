"""node_memory_seq008_learning_append_seq008_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from .存p_nm_st_s003_v001 import load_memory, save_memory
from .存p_nm_co_s001_v001 import MAX_RAW_ENTRIES
from .存p_nm_pr_s006_v001 import _rebuild_policy

def append_learning(
    root: Path,
    node: str,
    electron_id: str,
    task_seed: str,
    contribution_summary: str,
    credit_score: float,
    outcome_loss: float,
    operator_state_after: str = "unknown",
    rework_score: float = 0.0,
    deletion_ratio_after: float = 0.0,
) -> dict[str, Any]:
    """
    Append a learning entry for a node and rebuild its policy.

    Returns the updated node record (entries + policy).
    """
    memory = load_memory(root)
    node_record = memory.setdefault(node, {"entries": [], "policy": {}})

    entry = {
        "electron_id": electron_id,
        "task_seed": task_seed[:120],
        # ── observation (measured — drives scoring) ──
        "observation": {
            "credit_score": round(credit_score, 4),
            "outcome_loss": round(outcome_loss, 4),
            "rework_score": round(rework_score, 4),
            "deletion_ratio_after": round(deletion_ratio_after, 4),
            "operator_state_after": operator_state_after,
        },
        # ── hypothesis (LLM-generated — informational only, NOT used in scoring) ──
        "hypothesis": {
            "contribution_summary": contribution_summary[:200],
            "source": "llm_inference",
        },
        # Legacy flat fields kept for backward compat with existing policy rebuild
        "credit_score": round(credit_score, 4),
        "outcome_loss": round(outcome_loss, 4),
        "operator_state_after": operator_state_after,
        "rework_score": round(rework_score, 4),
        "deletion_ratio_after": round(deletion_ratio_after, 4),
        "contribution_summary": contribution_summary[:200],
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    node_record["entries"].append(entry)

    # Cap raw entries
    if len(node_record["entries"]) > MAX_RAW_ENTRIES:
        node_record["entries"] = node_record["entries"][-MAX_RAW_ENTRIES:]

    # Rebuild policy from entries
    node_record["policy"] = _rebuild_policy(node, node_record["entries"])

    memory[node] = node_record
    save_memory(root, memory)
    return node_record
