# ┌──────────────────────────────────────────────┐
# │  node_memory — per-node learning accumulation  │
# │  pigeon_brain/flow                             │
# └──────────────────────────────────────────────┘
# ── telemetry:pulse ──
# EDIT_TS:   2026-03-25T00:00:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  initial implementation
# ── /pulse ──
"""
The experience vault. Stores raw learning entries per node and maintains
compressed behavioral policies.

node_memory.json stores both:
  - raw entries: append-only log of every backward-pass signal per node
  - policy: compressed rolling score, top patterns, failure patterns

Exponential decay: rolling_score = historical * 0.9 + new_signal * 0.1
Policy is rebuilt after each backward pass from the raw entries.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 008 | VER: v001 | ~130 lines | ~1,100 tokens
# DESC:   per_node_learning_accumulation
# INTENT: backprop_impl
# LAST:   2026-03-25
# SESSIONS: 1
# ──────────────────────────────────────────────
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DECAY_ALPHA = 0.1          # new signal weight (1 - alpha = memory weight)
MIN_CONFIDENCE_SAMPLES = 5  # entries before policy is "confident"
MAX_RAW_ENTRIES = 200       # cap per node to prevent unbounded growth
MEMORY_FILE = "node_memory.json"


def _memory_path(root: Path) -> Path:
    return root / "pigeon_brain" / MEMORY_FILE


def load_memory(root: Path) -> dict[str, Any]:
    """Load the full node memory store."""
    p = _memory_path(root)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def save_memory(root: Path, memory: dict[str, Any]) -> None:
    """Persist node memory to disk."""
    p = _memory_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(memory, indent=2, default=str), encoding="utf-8")


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
        "contribution_summary": contribution_summary[:200],
        "credit_score": round(credit_score, 4),
        "outcome_loss": round(outcome_loss, 4),
        "operator_state_after": operator_state_after,
        "rework_score": round(rework_score, 4),
        "deletion_ratio_after": round(deletion_ratio_after, 4),
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


def _rebuild_policy(node: str, entries: list[dict]) -> dict[str, Any]:
    """Compress raw entries into a behavioral policy."""
    if not entries:
        return {}

    # Exponential moving average for rolling score
    score = 0.5  # prior
    for e in entries:
        signal = e["credit_score"] * (1.0 - e["outcome_loss"])
        score = score * (1.0 - DECAY_ALPHA) + signal * DECAY_ALPHA

    n = len(entries)
    confidence = min(n / MIN_CONFIDENCE_SAMPLES, 1.0)

    # Utilization = average credit score (proxy for "were my contributions used")
    avg_credit = sum(e["credit_score"] for e in entries) / n

    # Top effective patterns: entries with high credit + low loss
    effective = sorted(entries, key=lambda e: e["credit_score"] * (1.0 - e["outcome_loss"]), reverse=True)
    top_patterns = [e["contribution_summary"] for e in effective[:3] if e["credit_score"] > 0.3]

    # Failure patterns: entries with low credit or high loss
    failures = sorted(entries, key=lambda e: e["outcome_loss"] - e["credit_score"], reverse=True)
    fail_patterns = [e["contribution_summary"] for e in failures[:2] if e["outcome_loss"] > 0.5]

    # Behavioral directive
    directive = _synthesize_directive(node, score, top_patterns, fail_patterns)

    return {
        "node": node,
        "rolling_score": round(score, 4),
        "confidence": round(confidence, 4),
        "top_effective_patterns": top_patterns,
        "failure_patterns": fail_patterns,
        "utilization_rate": round(avg_credit, 4),
        "behavioral_directive": directive,
        "sample_count": n,
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


def _synthesize_directive(
    node: str,
    score: float,
    top_patterns: list[str],
    fail_patterns: list[str],
) -> str:
    """Generate a one-line behavioral instruction from patterns."""
    parts = []
    if score > 0.7:
        parts.append(f"{node}: high performer")
    elif score < 0.3:
        parts.append(f"{node}: struggling")
    else:
        parts.append(f"{node}: moderate")

    if top_patterns:
        parts.append(f"focus on: {top_patterns[0][:60]}")
    if fail_patterns:
        parts.append(f"avoid: {fail_patterns[0][:60]}")

    return "; ".join(parts)


def get_policy(root: Path, node: str) -> dict[str, Any]:
    """Get the compressed policy for a specific node."""
    memory = load_memory(root)
    record = memory.get(node, {})
    return record.get("policy", {})


def get_all_policies(root: Path) -> dict[str, dict]:
    """Get policies for all nodes that have learning history."""
    memory = load_memory(root)
    return {
        node: record.get("policy", {})
        for node, record in memory.items()
        if record.get("policy")
    }
