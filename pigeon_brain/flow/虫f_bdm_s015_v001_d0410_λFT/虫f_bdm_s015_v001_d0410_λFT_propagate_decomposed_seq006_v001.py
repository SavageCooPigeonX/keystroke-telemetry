"""虫f_bdm_s015_v001_d0410_λFT_propagate_decomposed_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 48 lines | ~469 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path

def propagate_through_veins(
    root: Path,
    manifests: list[BugManifest],
    max_depth: int = 3,
) -> list[BugManifest]:
    """BFS through import graph to populate affected_chain on each manifest.

    Resolves pigeon glyph names → graph English names via seq number, then
    walks the import dependency graph to find downstream importers.
    High-severity bugs (oc, hi) propagate further.
    """
    dependents = _load_graph_edges(root)   # {dependency: [importers]}
    seq_to_nodes = _build_seq_to_graph_nodes(root)

    for manifest in manifests:
        # Resolve origin name to graph node name(s) via seq
        m = _SEQ_RE.search(manifest.origin_module)
        origin_graph_names: list[str] = []
        if m:
            seq = int(m.group(1))
            origin_graph_names = seq_to_nodes.get(seq, [])
        # Also try direct match (handles English-named modules)
        if manifest.origin_module in dependents:
            origin_graph_names.append(manifest.origin_module)

        depth_limit = max_depth if manifest.severity >= 0.6 else 1
        visited: set[str] = set(origin_graph_names) | {manifest.origin_module}
        frontier = list(origin_graph_names)
        chain: list[str] = []

        for _ in range(depth_limit):
            next_frontier: list[str] = []
            for node in frontier:
                for downstream in dependents.get(node, []):
                    if downstream not in visited:
                        visited.add(downstream)
                        chain.append(downstream)
                        next_frontier.append(downstream)
            frontier = next_frontier
            if not frontier:
                break

        manifest.affected_chain = chain

    return manifests
