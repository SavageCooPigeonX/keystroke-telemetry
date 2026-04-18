"""numeric_surface_seq001_v001_clusters_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 35 lines | ~315 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import deque

def _detect_clusters(
    graph_nodes: dict, dual: dict[str, dict], threshold: float = 0.2
) -> dict[str, str]:
    """BFS clusters among nodes with dual_score or human_hesitation above threshold."""
    hot = set()
    for name in graph_nodes:
        dv = dual.get(name, {})
        score = max(dv.get("dual_score", 0), dv.get("human_hesitation", 0))
        if score > threshold:
            hot.add(name)
    visited: set[str] = set()
    clusters: dict[str, str] = {}
    cluster_id = 0

    for seed in sorted(hot):
        if seed in visited:
            continue
        cluster_id += 1
        label = f"C{cluster_id:02d}"
        queue: deque[str] = deque([seed])
        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            clusters[node] = label
            neighbors = set(graph_nodes.get(node, {}).get("edges_out", []))
            neighbors |= set(graph_nodes.get(node, {}).get("edges_in", []))
            for nb in neighbors:
                if nb in hot and nb not in visited:
                    queue.append(nb)
    return clusters
