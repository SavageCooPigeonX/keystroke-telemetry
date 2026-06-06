"""file_self_sim_learning_seq001_seq024_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq018_v001 import _relation_weight
from .file_self_sim_learning_seq001_seq037_v001 import _relationship_type
from .file_self_sim_learning_seq001_seq039_v001 import _line_count
from pathlib import Path
from typing import Any
import re

def _size_pressure(root: Path, rel: str, settings: dict[str, Any]) -> dict[str, Any]:
    line_count = _line_count(root, rel)
    soft = int(settings.get("soft_line_cap") or 200)
    warn = int(settings.get("warn_line_cap") or 300)
    hard = int(settings.get("hard_line_cap") or 500)
    if line_count <= soft:
        state = "ok"
    elif line_count <= warn:
        state = "over_soft"
    elif line_count <= hard:
        state = "warn"
    else:
        state = "critical"
    pressure = 0.0 if line_count <= soft else round(line_count / max(hard, 1), 3)
    return {
        "line_count": line_count,
        "soft_cap": soft,
        "warn_cap": warn,
        "hard_cap": hard,
        "state": state,
        "pressure": pressure,
        "needs_split_plan": line_count > soft,
    }


def _validation_confidence(tests: list[str], proposal: dict[str, Any]) -> float:
    score = 0.15
    if tests:
        score += min(len(tests), 4) * 0.18
    validation = proposal.get("cross_file_validation") or {}
    if validation.get("exists"):
        score += 0.12
    if validation.get("referenced_by"):
        score += 0.1
    ten_q = proposal.get("ten_q") or {}
    if ten_q.get("passed"):
        score += 0.15
    return round(min(score, 1.0), 3)


def _node_relationship_weight(rel: str, neighbors: list[str], sources: dict[str, Any]) -> float:
    weight = 0.0
    for neighbor in neighbors[:16]:
        weight += _relation_weight(_relationship_type(rel, neighbor, sources))
    return round(weight, 3)
