"""file_self_sim_learning_seq001_seq026_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq040_v001 import _dedupe
from pathlib import Path
from typing import Any
import re

def _neighbors_from_graph(graph: dict[str, Any], rel: str) -> list[str]:
    neighbors = []
    for edge in graph.get("edges") or []:
        if edge.get("from") == rel:
            neighbors.append(edge.get("to"))
        elif edge.get("to") == rel:
            neighbors.append(edge.get("from"))
    return [item for item in _dedupe(neighbors) if item][:12]


def _reason_not_to_split(rel: str, tests: list[str], neighbors: list[str]) -> str:
    reasons = []
    if not tests and rel.endswith(".py"):
        reasons.append("no mapped test gate yet")
    if len(neighbors) > 8:
        reasons.append("dense peer context; extract behind facade first")
    if Path(rel).name in {"__init__.py", "codex_compat.py"}:
        reasons.append("likely public facade/import surface")
    return "; ".join(reasons) or "no blocker; draft split plan behind stable imports"
