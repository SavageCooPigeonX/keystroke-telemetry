"""Extract the cognition graph from existing pigeon infrastructure.

Nodes = pigeon code files. Edges = import/call relationships.
Reads pigeon_registry.json + AST import analysis. Outputs adjacency list.
"""


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
    seen_edges = set()
    for name, node in nodes.items():
        fpath = root / node["path"]
        if not fpath.exists():
            continue
        imports = _extract_imports(fpath)
        for imp in imports:
            # Match imported module name to a registered node
            target = _resolve_import(imp, nodes, path_to_name)
            if target and target != name and (name, target) not in seen_edges:
                seen_edges.add((name, target))
                edges.append({"from": name, "to": target, "type": "import"})
                node["edges_out"].append(target)
                if target in nodes:
                    nodes[target]["edges_in"].append(name)

    # Wire intra-package edges from __init__.py files
    _wire_package_edges(root, nodes, path_to_name, edges, seen_edges)

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


def _wire_package_edges(root: Path, nodes: dict, path_to_name: dict,
                        edges: list, seen: set) -> None:
    """Wire sub-modules to their parent monolith via directory membership.

    Any registered file inside a package directory is connected to the
    parent monolith node (star topology). If no parent exists, sub-modules
    in the same directory are chained together.
    """
    # Group registered nodes by their parent directory
    dir_to_members: dict[str, list[str]] = {}
    for name, info in nodes.items():
        p = info["path"].replace("\\", "/")
        parts = p.rsplit("/", 1)
        if len(parts) == 2:
            dir_to_members.setdefault(parts[0], []).append(name)

    for pkg_dir, members in dir_to_members.items():
        if len(members) < 2:
            continue

        # Find the parent monolith node (lives outside pkg_dir, name matches)
        dir_base = pkg_dir.rsplit("/", 1)[-1]
        dir_clean = re.sub(r'_seq\d+.*$', '', dir_base)
        parent = None
        member_set = set(members)
        for name in nodes:
            if name in member_set:
                continue
            if re.sub(r'_seq\d+.*$', '', name) == dir_clean:
                parent = name
                break

        def _add_edge(a: str, b: str, etype: str = "package") -> None:
            if (a, b) not in seen:
                seen.add((a, b))
                edges.append({"from": a, "to": b, "type": etype})
                nodes[a]["edges_out"].append(b)
                nodes[b]["edges_in"].append(a)

        if parent:
            # Star topology: parent <-> each sub-module
            for sub in members:
                if sub == parent:
                    continue
                _add_edge(parent, sub)
                _add_edge(sub, parent)
        else:
            # No parent monolith — chain the sub-modules together
            chain = sorted(members)
            for i in range(len(chain) - 1):
                _add_edge(chain[i], chain[i + 1])


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
