"""虫f_bdm_s015_v001_d0410_λFT_loaders_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
from typing import Any
import json

def _load_registry(root: Path) -> list[dict]:
    p = root / REGISTRY_PATH
    if not p.exists():
        return []
    data = json.loads(p.read_text("utf-8"))
    return data.get("files", []) if isinstance(data, dict) else data


def _load_veins(root: Path) -> dict[str, Any]:
    p = root / VEINS_PATH
    if not p.exists():
        return {}
    return json.loads(p.read_text("utf-8"))


def _load_graph_edges(root: Path) -> dict[str, list[str]]:
    """Return {dependency: [importers_of_that_dependency]}.

    graph_cache edge format: {'from': importer, 'to': dependency, 'type': 'import'}
    If dependency has a bug, its importers inherit the affected context.
    So dependents[dependency] = [all modules that import it].
    """
    cache = root / "pigeon_brain" / "graph_cache.json"
    if not cache.exists():
        return {}
    graph = json.loads(cache.read_text("utf-8"))
    edges = graph.get("edges", [])
    dependents: dict[str, list[str]] = {}
    for edge in edges:
        importer = edge.get("from", "")
        dependency = edge.get("to", "")
        if importer and dependency:
            dependents.setdefault(dependency, []).append(importer)
    return dependents
