"""numeric_surface_seq001_v001_main_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v001 | 117 lines | ~1,081 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
import json

def generate_surface(root: Path) -> Path:
    """Build numeric_surface_seq001_v001.json — pure numeric topology of the codebase."""
    registry = _load_json(root / "pigeon_registry.json")
    graph = _load_or_rebuild_graph(root, registry)
    heat_map = _load_json(root / "file_heat_map.json")
    dual = _build_dual_lookup(root)

    graph_nodes = graph.get("nodes", {}) if isinstance(graph, dict) else {}
    reg_files = registry.get("files", []) if isinstance(registry, dict) else registry

    # Build name→registry lookup
    reg_by_name: dict[str, dict] = {}
    for f in (reg_files if isinstance(reg_files, list) else []):
        reg_by_name[f.get("name", "")] = f

    # Build operator heat from file_heat_map (avg hesitation)
    operator_heat: dict[str, float] = {}
    for mod_name, mod_data in (heat_map if isinstance(heat_map, dict) else {}).items():
        samples = mod_data.get("samples", [])
        if samples:
            recent = samples[-20:]
            avg_hes = sum(s.get("hes", 0) for s in recent) / len(recent)
            operator_heat[mod_name] = round(avg_hes, 3)

    now = datetime.now(timezone.utc)
    surface: dict[str, dict] = {}

    # All unique names: graph + registry
    all_names: set[str] = set(graph_nodes.keys())
    for f in (reg_files if isinstance(reg_files, list) else []):
        n = f.get("name", "")
        if n:
            all_names.add(n)

    for name in sorted(all_names):
        gnode = graph_nodes.get(name, {})
        reg = reg_by_name.get(name, {})
        dv = dual.get(name, {})

        seq = gnode.get("seq", 0) or reg.get("seq", 0)
        tokens = gnode.get("tokens", 0) or reg.get("tokens", 0)
        ver = gnode.get("ver", 0) or reg.get("ver", 0)
        bugs = reg.get("bug_keys", [])
        intent_code = reg.get("intent_code", "")

        # Edges as name references (topology stays name-addressed)
        edges_out = gnode.get("edges_out", [])
        edges_in = gnode.get("edges_in", [])

        # Heat: best of dual_score, human_hesitation, operator_heat
        dual_score = dv.get("dual_score", 0)
        human_hes = dv.get("human_hesitation", 0)
        op_heat = operator_heat.get(name, 0)
        combined_heat = round(max(dual_score, human_hes, op_heat), 3)

        node_entry = {
            "seq": seq,
            "edges_out": sorted(edges_out),
            "edges_in": sorted(edges_in),
            "degree": len(edges_out) + len(edges_in),
            "heat": combined_heat,
            "dual_score": round(dual_score, 3),
            "tokens": tokens,
            "ver": ver,
            "bugs": bugs,
            "intent": intent_code,
        }

        # Enrich from dual_view if available
        if dv:
            node_entry["personality"] = dv.get("personality", "")
            deaths = dv.get("agent_deaths", 0)
            if deaths:
                node_entry["deaths"] = deaths
            fears = dv.get("fears", [])
            if fears:
                node_entry["fears"] = fears

        surface[name] = node_entry

    # Detect clusters using graph + dual_view heat
    clusters = _detect_clusters(graph_nodes, dual)
    for name, cluster_label in clusters.items():
        if name in surface:
            surface[name]["cluster"] = cluster_label

    # Compressed traversal
    traversal = _compressed_traversal(surface)

    # Stats
    total_edges = sum(len(n.get("edges_out", [])) for n in surface.values())
    hot_count = sum(1 for d in surface.values() if d.get("heat", 0) > 0.2)
    bugged_count = sum(1 for d in surface.values() if d.get("bugs"))
    cluster_set = set(v.get("cluster", "") for v in surface.values()) - {""}

    output = {
        "schema": "numeric_surface_seq001_v001/v1",
        "generated": now.isoformat(),
        "stats": {
            "nodes": len(surface),
            "total_edges": total_edges,
            "hot_nodes": hot_count,
            "bugged_nodes": bugged_count,
            "clusters": len(cluster_set),
        },
        "traversal": traversal,
        "nodes": surface,
    }

    out_path = root / "logs" / "numeric_surface_seq001_v001.json"
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return out_path
