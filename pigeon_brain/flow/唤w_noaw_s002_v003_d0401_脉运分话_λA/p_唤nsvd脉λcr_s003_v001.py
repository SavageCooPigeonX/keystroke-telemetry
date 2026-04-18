"""唤w_noaw_s002_v003_d0401_脉运分话_λA_compute_relevance_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 41 lines | ~327 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from typing import Any
import re

def _compute_relevance(
    task_tokens: set[str],
    node: dict[str, Any],
    path_nodes: list[str],
) -> float:
    """Score 0.0–1.0 how relevant this node is to the current packet."""
    score = 0.0

    # 1. Name / description overlap with task
    node_name = node.get("name", "")
    desc = node.get("desc", "")
    node_tokens = _tokenize(f"{node_name} {desc}")
    if task_tokens and node_tokens:
        overlap = len(task_tokens & node_tokens)
        score += min(overlap * 0.2, 0.5)

    # 2. Fear keywords match task
    fears = node.get("fears", [])
    fear_text = " ".join(fears)
    fear_tokens = _tokenize(fear_text)
    fear_overlap = len(task_tokens & fear_tokens)
    score += min(fear_overlap * FEAR_KEYWORD_BOOST, 0.3)

    # 3. High heat = auto-relevant
    dual = node.get("dual_score", 0.0)
    if dual >= HEAT_AUTO_RELEVANT:
        score = max(score, 0.6)

    # 4. Direct dependency on path members
    edges_out = set(node.get("edges_out", []))
    edges_in = set(node.get("edges_in", []))
    connected = edges_out | edges_in
    path_set = set(path_nodes)
    if connected & path_set:
        score += 0.2

    return min(score, 1.0)
