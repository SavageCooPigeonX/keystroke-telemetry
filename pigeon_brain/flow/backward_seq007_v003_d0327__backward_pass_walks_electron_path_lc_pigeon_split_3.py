# ┌──────────────────────────────────────────────┐
# │  backward — gradient distribution through the  │
# │  code graph. pigeon_brain/flow                 │
# └──────────────────────────────────────────────┘
# ── telemetry:pulse ──
# EDIT_TS:   2026-03-27T04:30:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  wire DeepSeek as backprop engine
# ── /pulse ──
"""Backward pass: walks electron path in REVERSE, computes credit/node,
writes to node_memory. DeepSeek generates rich contribution analysis.
Loss = rework*0.4 + del*0.3 + frustration*0.2 + ignored*0.1.
Credit = overlap*0.35 + position*0.25 + relevance*0.25 + downstream*0.15.
Cost: ~$0.003 per backward pass (1 DeepSeek call for analysis)."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v003 | 273 lines | ~2,500 tokens
# DESC:   backward_pass_walks_electron_path
# INTENT: pigeon_split_3
# LAST:   2026-03-27 @ fd07906
# SESSIONS: 2
# ──────────────────────────────────────────────
# ── pigeon: SEQ 007 | v001 | backprop_impl | 2026-03-25 ──
from __future__ import annotations

import json
import logging
import re
import uuid
from pathlib import Path
from typing import Any

from .node_memory_seq008_v001_d0325__per_node_learning_accumulation_lc_backprop_impl import (
    append_learning,
)

logger = logging.getLogger(__name__)

FLOW_LOG = "flow_log.jsonl"
STATE_FRUSTRATION = {"frustrated", "confused", "struggling"}


def _deepseek_analyze_backward(
    task_seed: str, path: list[str], accumulated: list[dict],
    journal_entry: dict[str, Any], loss: float,
) -> dict[str, Any]:
    """Use DeepSeek to generate rich backward-pass analysis.

    Returns {node_analyses: [{node, summary, directive, failure_reason}...],
             system_insight: str, cost: float}
    Falls back to empty analysis if DeepSeek unavailable.
    """
    try:
        from pigeon_compiler.integrations.deepseek_adapter_seq001_v006_d0322__deepseek_api_client_lc_stage_78_hook import (
            deepseek_query,
        )
    except (ImportError, ValueError):
        return {"node_analyses": [], "system_insight": "", "cost": 0.0}

    node_block = "\n".join(
        f"  - {n.get('node','?')}: dual={n.get('dual_score',0):.2f}, "
        f"fears={n.get('fears',[])[:2]}, relevance={n.get('relevance',0):.2f}"
        for n in accumulated[:15]
    )
    state = journal_entry.get("cognitive_state", "unknown")
    rework = journal_entry.get("rework_score", 0.0)
    prompt = f"""Backward pass analysis for a code-graph flow engine.

Task: "{task_seed}"
Path traversed: {' → '.join(path[:15])}
Loss: {loss:.3f} (0=perfect, 1=total failure)
Operator state after: {state}
Rework score: {rework:.2f}

Nodes that contributed:
{node_block}

For each node, write a 1-line contribution summary and 1-line behavioral directive.
If loss > 0.5, identify which node(s) failed and why.
End with a 1-line system-level insight.

Respond as JSON: {{"node_analyses": [{{"node": "...", "summary": "...", "directive": "...", "failure_reason": "..."}}], "system_insight": "..."}}"""

    try:
        result = deepseek_query(
            prompt=prompt,
            system="You are a neural graph backward-pass analyzer. Be precise and terse.",
            temperature=0.1,
            max_tokens=800,
        )
        text = result.get("content", "")
        # Extract JSON from response
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            analysis = json.loads(match.group())
            analysis["cost"] = result.get("cost", 0.0)
            return analysis
    except Exception as e:
        logger.warning(f"[backward] DeepSeek analysis failed: {e}")

    return {"node_analyses": [], "system_insight": "", "cost": 0.0}


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


def _append_insight(root: Path, electron_id: str, insight: str, loss: float) -> None:
    """Append a DeepSeek system insight to the flow log."""
    p = _flow_log_path(root)
    entry = {
        "type": "backward_insight",
        "electron_id": electron_id,
        "insight": insight[:300],
        "loss": round(loss, 4),
    }
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")
