"""脉运w_vt_s006_v003_d0401_唤分话_λA_transport_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 37 lines | ~304 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from .包p_cpk_s001_v002_d0324_缩分话_λε import ContextPacket
from typing import Any

def transport(
    packet: ContextPacket,
    from_node: str,
    to_node: str,
    graph_data: dict[str, Any],
    veins_data: dict[str, Any] | None = None,
) -> ContextPacket:
    """
    Move a packet along an edge from from_node to to_node.

    Modifies packet importance and heat based on edge health.
    Returns the same packet (mutated).
    """
    if not packet.alive:
        return packet

    # Build edge health from vein data if available
    edge_health = _edge_health(from_node, to_node, graph_data, veins_data)

    if edge_health < 0:
        # Dead edge — clot-to-clot or broken import
        packet.dead_vein_warnings.append(f"DEAD VEIN: {from_node} → {to_node}")
        packet.heat += DEAD_VEIN_HEAT

    elif edge_health < WEAK_THRESHOLD:
        # Weak connection — signal decays
        packet.importance *= WEAK_DECAY

    elif edge_health > STRONG_THRESHOLD:
        # Strong artery — signal amplifies (capped at 1.0)
        packet.importance = min(packet.importance * STRONG_AMPLIFY, 1.0)

    return packet
