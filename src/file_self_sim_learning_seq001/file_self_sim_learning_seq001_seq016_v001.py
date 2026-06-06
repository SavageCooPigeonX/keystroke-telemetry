"""file_self_sim_learning_seq001_seq016_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq018_v001 import _add_weighted_edge
from .file_self_sim_learning_seq001_seq018_v001 import _relation_weight
from .file_self_sim_learning_seq001_seq038_v001 import _clean_rel
from .file_self_sim_learning_seq001_seq041_v001 import _now
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
import re

def _weighted_relationship_graph(
    root: Path,
    sources: dict[str, Any],
    wake_order: list[dict[str, Any]],
    packets: list[dict[str, Any]],
) -> dict[str, Any]:
    edges: dict[tuple[str, str, str], dict[str, Any]] = {}

    for edge in (sources.get("council") or {}).get("relationships") or []:
        _add_weighted_edge(
            edges,
            edge.get("from"),
            edge.get("to"),
            str(edge.get("type") or "peer"),
            str(edge.get("reason") or "file council relationship"),
            _relation_weight(str(edge.get("type") or "peer")),
        )

    for pack in (sources.get("council") or {}).get("context_packs") or []:
        files = [_clean_rel(item) for item in pack.get("files") or []]
        files = [item for item in files if item]
        for index, left in enumerate(files[:10]):
            for right in files[index + 1:10]:
                _add_weighted_edge(edges, left, right, "context_pack", str(pack.get("pack_id") or "context pack"), 0.35)

    for node in wake_order:
        rel = node.get("file")
        for vein in node.get("context_veins") or []:
            _add_weighted_edge(
                edges,
                rel,
                vein.get("file"),
                str(vein.get("relation") or "peer_context"),
                str(vein.get("reason") or "wake context vein"),
                _relation_weight(str(vein.get("relation") or "peer_context")),
            )

    for packet in packets:
        rel = packet.get("file")
        for target in packet.get("backward_learning_targets") or []:
            if not isinstance(target, dict):
                continue
            _add_weighted_edge(edges, rel, target.get("file"), "backward_target", target.get("learn", ""), 0.45)

    for outcome in sources.get("learning_outcomes") or []:
        reward = float(outcome.get("reward") or 0)
        rel = outcome.get("file")
        for target in outcome.get("backward_targets") or []:
            if isinstance(target, dict):
                _add_weighted_edge(
                    edges,
                    rel,
                    target.get("file"),
                    "learned_peer_outcome",
                    str(outcome.get("outcome") or "learning outcome"),
                    0.2 + min(max(reward, 0.0), 1.0) * 0.6,
                )

    edge_rows = sorted(edges.values(), key=lambda item: item.get("weight", 0), reverse=True)
    node_weights: dict[str, float] = defaultdict(float)
    for edge in edge_rows:
        node_weights[edge["from"]] += float(edge["weight"])
        node_weights[edge["to"]] += float(edge["weight"])

    nodes = [
        {"file": rel, "weighted_degree": round(weight, 3)}
        for rel, weight in sorted(node_weights.items(), key=lambda item: item[1], reverse=True)
    ]
    return {
        "schema": "weighted_file_relationship_graph/v1",
        "ts": _now(),
        "learning_rule": "peer outcomes alter future routing weight; they do not authorize source writes",
        "nodes": nodes[:80],
        "edges": edge_rows[:160],
    }
