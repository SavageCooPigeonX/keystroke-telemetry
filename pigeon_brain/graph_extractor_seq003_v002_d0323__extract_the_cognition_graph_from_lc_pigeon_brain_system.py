# @pigeon: seq=003 | role=graph_extractor | depends=[models] | exports=[build_graph,load_graph] | tokens=~500
"""Extract the cognition graph from existing pigeon infrastructure.

Nodes = pigeon code files. Edges = import/call relationships.
Reads pigeon_registry.json + AST import analysis. Outputs adjacency list.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v002 | 132 lines | ~1,116 tokens
# DESC:   extract_the_cognition_graph_from
# INTENT: pigeon_brain_system
# LAST:   2026-03-23 @ 465cbfa
# SESSIONS: 1
# ──────────────────────────────────────────────

import ast
import json
import re
from pathlib import Path


def build_graph(root: Path) -> dict:
    """Build adjacency list from pigeon registry + AST imports.

    Returns {"nodes": {name: {...}}, "edges": [...], "total": int}
    """
    registry_path = root / "pigeon_registry.json"
    if not registry_path.exists():
        return {"nodes": {}, "edges": [], "total": 0}

    registry = json.loads(registry_path.read_text("utf-8"))
    files = registry.get("files", [])

    nodes = {}
    path_to_name = {}

    for entry in files:
        name = entry.get("name", "")
        if not name:
            continue
        nodes[name] = {
            "path": entry.get("path", ""),
            "seq": entry.get("seq", 0),
            "ver": entry.get("ver", 1),
            "tokens": entry.get("tokens", 0),
            "desc": entry.get("desc", ""),
            "edges_out": [],
            "edges_in": [],
            "heat": 0.0,
            "electron_deaths": 0,
        }
        path_to_name[entry.get("path", "")] = name

    # Extract import edges via AST
    edges = []
    for name, node in nodes.items():
        fpath = root / node["path"]
        if not fpath.exists():
            continue
        imports = _extract_imports(fpath)
        for imp in imports:
            # Match imported module name to a registered node
            target = _resolve_import(imp, nodes, path_to_name)
            if target and target != name:
                edges.append({"from": name, "to": target, "type": "import"})
                node["edges_out"].append(target)
                if target in nodes:
                    nodes[target]["edges_in"].append(name)

    return {"nodes": nodes, "edges": edges, "total": len(nodes)}


def _extract_imports(filepath: Path) -> list[str]:
    """Extract all import targets from a Python file via AST."""
    try:
        source = filepath.read_text("utf-8", errors="replace")
        tree = ast.parse(source, filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError):
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def _resolve_import(module_name: str, nodes: dict, path_map: dict) -> str | None:
    """Try to match an import string to a known pigeon module name."""
    # Direct name match
    base = module_name.split(".")[-1]
    # Strip version/date suffixes for fuzzy match
    clean = re.sub(r'_seq\d+.*$', '', base)
    for name in nodes:
        name_clean = re.sub(r'_seq\d+.*$', '', name)
        if name_clean == clean or name == base:
            return name
    return None


def load_graph(root: Path) -> dict:
    """Load cached graph or rebuild."""
    cache = root / "pigeon_brain" / "graph_cache.json"
    if cache.exists():
        try:
            return json.loads(cache.read_text("utf-8"))
        except Exception:
            pass
    graph = build_graph(root)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(graph, indent=2), encoding="utf-8")
    return graph


def graph_stats(graph: dict) -> dict:
    """Quick summary stats from a graph."""
    nodes = graph.get("nodes", {})
    edges = graph.get("edges", [])
    if not nodes:
        return {"total_nodes": 0, "total_edges": 0}

    out_degrees = [len(n.get("edges_out", [])) for n in nodes.values()]
    in_degrees = [len(n.get("edges_in", [])) for n in nodes.values()]

    bottlenecks = sorted(nodes.items(),
                         key=lambda x: len(x[1].get("edges_in", [])),
                         reverse=True)[:5]

    return {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "avg_out_degree": round(sum(out_degrees) / max(len(out_degrees), 1), 1),
        "max_in_degree": max(in_degrees) if in_degrees else 0,
        "bottlenecks": [{"name": b[0], "in_degree": len(b[1].get("edges_in", []))}
                        for b in bottlenecks],
    }
