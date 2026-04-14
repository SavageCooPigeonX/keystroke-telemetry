"""脉运w_vt_s006_v003_d0401_唤分话_λA_edge_health_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 42 lines | ~308 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from typing import Any

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
