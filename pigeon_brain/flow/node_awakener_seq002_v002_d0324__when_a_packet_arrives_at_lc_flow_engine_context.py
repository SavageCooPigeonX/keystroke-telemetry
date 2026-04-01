# ┌──────────────────────────────────────────────┐
# │  node_awakener — wakes a node, gates relevance │
# │  pigeon_brain/flow                              │
# └──────────────────────────────────────────────┘
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# ── /pulse ──
"""
When a packet arrives at a node, the node WAKES UP.

But not every node contributes. Relevance gating is the critical
constraint: if the node isn't relevant to the flowing packet, it
passes through silently. If everything contributes, nothing matters.

Relevance is computed from:
  - keyword overlap between task_seed and node desc/fears/personality
  - heat threshold (hot nodes are always relevant)
  - direct dependency (if the node imports or is imported by a path member)
"""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v002 | 152 lines | ~1,186 tokens
# DESC:   when_a_packet_arrives_at
# INTENT: flow_engine_context
# LAST:   2026-03-24 @ c0caa0a
# SESSIONS: 1
# ──────────────────────────────────────────────
from __future__ import annotations

import re
from typing import Any

from .context_packet_seq001_v002_d0324__包逆流_the_contextpacket_is_the_unit_lc_flow_engine_context import ContextPacket, NodeIntel

RELEVANCE_THRESHOLD = 0.3
HEAT_AUTO_RELEVANT = 0.5     # dual_score above this = always relevant
FEAR_KEYWORD_BOOST = 0.25    # bonus for fear keywords matching task


def _tokenize(text: str) -> set[str]:
    """Extract lowercase word tokens from text, splitting on underscores."""
    raw = re.findall(r"[a-z_]{3,}", text.lower())
    tokens: set[str] = set()
    for tok in raw:
        tokens.add(tok)
        for part in tok.split("_"):
            if len(part) >= 3:
                tokens.add(part)
    return tokens


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


def awaken(
    node_name: str,
    packet: ContextPacket,
    graph_data: dict[str, Any],
) -> bool:
    """
    Wake a node and let it contribute to the packet.

    Returns True if the node contributed, False if it was gated out.
    The packet is mutated in place.
    """
    if not packet.alive:
        return False

    nodes = graph_data.get("nodes", {})
    node = nodes.get(node_name)
    if node is None:
        return False

    # Loop detection
    if packet.visit(node_name):
        return False

    # Relevance gating — the critical constraint
    task_tokens = _tokenize(packet.task_seed)
    relevance = _compute_relevance(task_tokens, node, packet.path)

    # Origin node always contributes
    if not packet.path:
        relevance = max(relevance, 1.0)

    if relevance < RELEVANCE_THRESHOLD:
        # Node stays asleep — packet passes through silently
        packet.path.append(node_name)
        packet.step()
        return False

    # NODE AWAKENS — build intelligence
    intel = NodeIntel(
        node=node_name,
        version=node.get("ver", 1),
        personality=node.get("personality", ""),
        fears=node.get("fears", []),
        human_hesitation=node.get("human_hesitation", 0.0),
        agent_death_rate=node.get("death_rate", 0.0),
        dual_score=node.get("dual_score", 0.0),
        dead_limbs=node.get("agent_deaths", 0),
        drama=node.get("ver", 1),
        slumber_parties=node.get("partners", []),
        clot_signals=node.get("clot_signals", []),
        vein_score=node.get("vein_score", 0.5),
        relevance=relevance,
    )

    # Append to packet
    packet.append_intel(intel)
    packet.path.append(node_name)

    # Narrative fragment from personality + fears
    if intel.fears:
        top_fear = intel.fears[0]
        frag = f"{node_name} (v{intel.version}, {intel.personality}): fears '{top_fear}'"
        if intel.dual_score > 0.5:
            frag += f" [CRITICAL dual={intel.dual_score:.2f}]"
        packet.narrative_fragments.append(frag)

    packet.step()
    return True
