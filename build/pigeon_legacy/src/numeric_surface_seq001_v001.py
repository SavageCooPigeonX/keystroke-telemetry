"""numeric_surface_seq001_v001 — Projects the codebase into a pure numeric topology.

Reads graph_cache.json + file_heat_map.json + pigeon_registry.json
to generate numeric_surface_seq001_v001.json — the numeric shadow of the codebase.

LLMs read this FIRST. No text. Just addresses, edges, scores, clusters.

    py -c "from src.numeric_surface_seq001_v001 import generate_surface; generate_surface(Path('.'))"
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone
from collections import deque


def _load_json(path: Path) -> dict | list:
    if path.exists():
        return json.loads(path.read_text("utf-8"))
    return {}


def _rebuild_graph_cache(root: Path) -> dict:
    """Rebuild graph_cache.json from the latest graph extractor when stale."""
    import importlib.util

    brain_dir = root / "pigeon_brain"
    cache_path = brain_dir / "graph_cache.json"
    candidates = sorted(
        brain_dir.glob("图p_ge_s*_v*.py"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for candidate in candidates:
        try:
            spec = importlib.util.spec_from_file_location("_graph_extractor", candidate)
            if not spec or not spec.loader:
                continue
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            build_graph = getattr(mod, "build_graph", None)
            if not callable(build_graph):
                continue
            graph = build_graph(root)
            if isinstance(graph, dict) and isinstance(graph.get("nodes"), dict):
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
                return graph
        except Exception:
            continue
    return {}


def _load_or_rebuild_graph(root: Path, registry: dict | list) -> dict:
    """Load graph_cache.json, but self-heal when coverage is obviously stale."""
    cache_path = root / "pigeon_brain" / "graph_cache.json"
    graph = _load_json(cache_path)
    if not isinstance(graph, dict):
        graph = {}
    nodes = graph.get("nodes", {}) if isinstance(graph.get("nodes"), dict) else {}

    reg_files = registry.get("files", []) if isinstance(registry, dict) else registry
    reg_names = {
        f.get("name", "")
        for f in (reg_files if isinstance(reg_files, list) else [])
        if f.get("name")
    }
    missing = reg_names - set(nodes)

    cache_stale = not cache_path.exists()
    if not cache_stale and (root / "pigeon_registry.json").exists():
        try:
            cache_stale = cache_path.stat().st_mtime < (root / "pigeon_registry.json").stat().st_mtime
        except OSError:
            cache_stale = False

    coverage_bad = bool(reg_names) and len(missing) > max(10, int(len(reg_names) * 0.05))
    if not cache_stale and not coverage_bad:
        return graph

    rebuilt = _rebuild_graph_cache(root)
    return rebuilt or graph


def _build_dual_lookup(root: Path) -> dict[str, dict]:
    """Load dual_view.json and return name→node dict."""
    dv = root / "pigeon_brain" / "dual_view.json"
    if not dv.exists():
        return {}
    raw = json.loads(dv.read_text("utf-8"))
    nodes = raw.get("nodes", []) if isinstance(raw, dict) else []
    return {n["name"]: n for n in nodes if "name" in n}


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


def _compressed_traversal(surface: dict, top_n: int = 12) -> list[str]:
    """Traversal strings for highest-heat nodes using addresses."""
    ranked = sorted(surface.items(), key=lambda x: -x[1].get("heat", 0))[:top_n]
    paths = []
    for addr, data in ranked:
        edges = data.get("edges_out", [])
        if not edges:
            paths.append(addr)
            continue
        chain = " > ".join(edges[:5])
        paths.append(f"{addr} > {chain}")
    return paths


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


if __name__ == "__main__":
    p = generate_surface(Path("."))
    print(f"Generated: {p}")
