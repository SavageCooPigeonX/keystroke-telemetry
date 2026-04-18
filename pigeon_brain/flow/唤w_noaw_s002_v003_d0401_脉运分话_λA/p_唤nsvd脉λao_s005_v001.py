"""唤w_noaw_s002_v003_d0401_脉运分话_λA_awaken_orchestrator_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 73 lines | ~569 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from .包p_cpk_s001_v002_d0324_缩分话_λε import ContextPacket, NodeIntel
from typing import Any
import re

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
