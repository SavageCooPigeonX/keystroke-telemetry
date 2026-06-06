"""file_self_sim_learning_seq001_seq018_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq038_v001 import _clean_rel
from .file_self_sim_learning_seq001_seq040_v001 import _dedupe
from typing import Any
import re

def _add_weighted_edge(
    edges: dict[tuple[str, str, str], dict[str, Any]],
    left: Any,
    right: Any,
    relation: str,
    reason: str,
    weight: float,
) -> None:
    a = _clean_rel(left)
    b = _clean_rel(right)
    if not a or not b or a == b:
        return
    first, second = sorted([a, b])
    key = (first, second, relation)
    edge = edges.setdefault(key, {
        "from": first,
        "to": second,
        "relation": relation,
        "weight": 0.0,
        "evidence": [],
    })
    edge["weight"] = round(float(edge.get("weight", 0)) + float(weight), 4)
    if reason:
        edge["evidence"].append(reason[:140])
        edge["evidence"] = _dedupe(edge["evidence"])[-5:]


def _relation_weight(relation: str) -> float:
    return {
        "beef": 1.4,
        "friendship": 1.15,
        "import": 1.05,
        "validator": 1.0,
        "manifest": 0.85,
        "backward_target": 0.7,
        "learned_peer_outcome": 0.65,
        "context_pack": 0.35,
    }.get(str(relation or "peer_context"), 0.55)
