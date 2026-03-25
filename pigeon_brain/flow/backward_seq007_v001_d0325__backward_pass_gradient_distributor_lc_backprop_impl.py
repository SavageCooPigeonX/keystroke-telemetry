# ┌──────────────────────────────────────────────┐
# │  backward — gradient distribution through the  │
# │  code graph. pigeon_brain/flow                 │
# └──────────────────────────────────────────────┘
# ── telemetry:pulse ──
# EDIT_TS:   2026-03-25T00:00:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  trim to 200 lines
# ── /pulse ──
"""Backward pass: walks electron path in REVERSE, computes credit/node,
writes to node_memory. Loss = rework*0.4 + del*0.3 + frustration*0.2 +
ignored*0.1. Credit = overlap*0.35 + position*0.25 + relevance*0.25 +
downstream*0.15. Cost: $0.00."""
# ── pigeon: SEQ 007 | v001 | backprop_impl | 2026-03-25 ──
from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any

from .node_memory_seq008_v001_d0325__per_node_learning_accumulation_lc_backprop_impl import (
    append_learning,
)

FLOW_LOG = "flow_log.jsonl"
STATE_FRUSTRATION = {"frustrated", "confused", "struggling"}


def _flow_log_path(root: Path) -> Path:
    return root / "pigeon_brain" / FLOW_LOG


def log_forward_pass(root: Path, packet_summary: dict[str, Any]) -> str:
    """Record a forward pass in the flow log. Returns the electron_id."""
    electron_id = packet_summary.get("electron_id") or uuid.uuid4().hex[:12]
    packet_summary["electron_id"] = electron_id
    p = _flow_log_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(packet_summary, default=str) + "\n")
    return electron_id


def _load_forward_path(root: Path, electron_id: str) -> dict[str, Any] | None:
    """Find a forward pass record by electron_id."""
    p = _flow_log_path(root)
    if not p.exists():
        return None
    for line in reversed(p.read_text(encoding="utf-8").strip().splitlines()):
        try:
            record = json.loads(line)
            if record.get("electron_id") == electron_id:
                return record
        except json.JSONDecodeError:
            continue
    return None


def compute_loss(journal_entry: dict[str, Any]) -> float:
    """Composite loss from a prompt journal entry. Lower is better (0.0–1.0)."""
    signals = journal_entry.get("signals", {})
    rework = journal_entry.get("rework_score", 0.0)
    del_ratio = signals.get("deletion_ratio", 0.0)
    state = journal_entry.get("cognitive_state", "unknown")
    frustration = 1.0 if state in STATE_FRUSTRATION else 0.0
    ignored = max(del_ratio, rework) * 0.5
    loss = rework * 0.4 + del_ratio * 0.3 + frustration * 0.2 + ignored * 0.1
    return min(max(loss, 0.0), 1.0)


def _tokenize(text: str) -> set[str]:
    """Extract lowercase word tokens from text."""
    raw = re.findall(r"[a-z_]{3,}", text.lower())
    tokens: set[str] = set()
    for tok in raw:
        tokens.add(tok)
        for part in tok.split("_"):
            if len(part) >= 3:
                tokens.add(part)
    return tokens


def _compute_credit(
    node_intel: dict[str, Any], position: int,
    path_length: int, fix_tokens: set[str],
) -> float:
    """Weighted credit attribution for a single node. Returns 0.0–1.0."""
    node_name = node_intel.get("node", "")
    fears = node_intel.get("fears", [])
    node_tokens = _tokenize(f"{node_name} {' '.join(fears)}")
    overlap = (len(fix_tokens & node_tokens) / max(len(fix_tokens), 1)
               if fix_tokens and node_tokens else 0.2)
    position_factor = 1.0 - (position / max(path_length, 1)) * 0.5
    relevance = node_intel.get("relevance", 0.5)
    downstream = min(node_intel.get("dual_score", 0.0) * 1.5, 1.0)
    credit = overlap * 0.35 + position_factor * 0.25 + relevance * 0.25 + downstream * 0.15
    return min(max(credit, 0.0), 1.0)


def backward_pass(
    root: Path, electron_id: str,
    journal_entry: dict[str, Any], fix_context: str = "",
) -> list[dict[str, Any]]:
    """Run backward pass for a completed electron. Returns learning results."""
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
    results = []
    path_len = len(path)

    # Walk path in REVERSE
    for position, node_name in enumerate(reversed(path)):
        intel = intel_by_node.get(node_name)
        if intel is None:
            continue  # node was on path but didn't contribute (gated out)

        credit = _compute_credit(intel, position, path_len, fix_tokens)
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
        results.append({"node": node_name, "credit": credit, "loss": loss})

    return results
