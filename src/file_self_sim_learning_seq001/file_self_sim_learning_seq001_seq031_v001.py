"""file_self_sim_learning_seq001_seq031_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq032_v001 import _local_import_neighbors
from .file_self_sim_learning_seq001_seq038_v001 import _clean_rel
from .file_self_sim_learning_seq001_seq040_v001 import _dedupe
from pathlib import Path
from typing import Any
import re

def _history_count_for_file(rel: str, sources: dict[str, Any]) -> int:
    return sum(
        1 for row in (sources.get("dead_pairs") or [])
        if _clean_rel(row.get("new_path") or row.get("old_path")) == rel
    )


def _neighbors_for_file(root: Path, rel: str, proposal: dict[str, Any], sources: dict[str, Any]) -> list[str]:
    neighbors: list[str] = []
    neighbors.extend(_clean_rel(item) for item in proposal.get("context_injection") or [])
    validation = proposal.get("cross_file_validation") or {}
    neighbors.extend(_clean_rel(item) for item in validation.get("referenced_by") or [])
    neighbors.extend(_local_import_neighbors(root, rel))
    for edge in (sources.get("council") or {}).get("relationships") or []:
        left = _clean_rel(edge.get("from"))
        right = _clean_rel(edge.get("to"))
        if left == rel:
            neighbors.append(right)
        elif right == rel:
            neighbors.append(left)
    for pack in (sources.get("council") or {}).get("context_packs") or []:
        files = [_clean_rel(item) for item in pack.get("files") or []]
        if rel in files:
            neighbors.extend(files)
    return [item for item in _dedupe(neighbors) if item and item != rel][:16]
