# ┌──────────────────────────────────────────────┐
# │  vein_transport — edge traversal with effects  │
# │  pigeon_brain/flow                             │
# └──────────────────────────────────────────────┘
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# ── /pulse ──
"""
As a packet flows along an edge (vein), the edge modifies the signal.

Strong veins (high-traffic, critical arteries) amplify.
Weak veins (rarely traversed) decay.
Dead veins (clot connections) add warnings and increase heat.

The vein is not passive plumbing. It's a transformation channel.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v002 | 120 lines | ~899 tokens
# DESC:   as_a_packet_flows_along
# INTENT: flow_engine_context
# LAST:   2026-03-24 @ c0caa0a
# SESSIONS: 1
# ──────────────────────────────────────────────
from __future__ import annotations

from typing import Any

from .context_packet_seq001_v002_d0324__包逆流_the_contextpacket_is_the_unit_lc_flow_engine_context import ContextPacket

DEAD_VEIN_HEAT = 0.15
WEAK_THRESHOLD = 0.3
STRONG_THRESHOLD = 0.8
WEAK_DECAY = 0.93
STRONG_AMPLIFY = 1.05


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


def _edge_health(
    from_node: str,
    to_node: str,
    graph_data: dict[str, Any],
    veins_data: dict[str, Any] | None,
) -> float:
    """
    Compute health score for an edge.

    Uses vein scores of both endpoints.  Returns -1.0 for dead edges.
    Returns 0.0–1.0 for live edges.
    """
    nodes = graph_data.get("nodes", {})
    src = nodes.get(from_node, {})
    dst = nodes.get(to_node, {})

    # Check if edge exists in either direction
    fwd = to_node in src.get("edges_out", [])
    rev = from_node in dst.get("edges_out", [])
    if not fwd and not rev:
        return -1.0

    if veins_data is None:
        # No vein data — assume neutral
        return 0.5

    # Build a lookup from the veins data
    vein_lookup = _build_vein_lookup(veins_data)

    src_vein = vein_lookup.get(from_node, 0.5)
    dst_vein = vein_lookup.get(to_node, 0.5)

    # Both clots = dead edge
    clot_lookup = _build_clot_set(veins_data)
    if from_node in clot_lookup and to_node in clot_lookup:
        return -1.0

    # Average of both endpoints' vein scores
    return (src_vein + dst_vein) / 2


def _build_vein_lookup(veins_data: dict[str, Any]) -> dict[str, float]:
    """Extract module → vein_score from veins JSON."""
    lookup: dict[str, float] = {}
    for node in veins_data.get("arteries", []):
        lookup[node["module"]] = node.get("vein_score", 1.0)
    for node in veins_data.get("clots", []):
        lookup[node["module"]] = node.get("vein_score", 0.0)
    return lookup


def _build_clot_set(veins_data: dict[str, Any]) -> set[str]:
    """Extract set of clot module names."""
    return {n["module"] for n in veins_data.get("clots", [])}
