"""file_self_sim_learning_seq001_seq037_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq038_v001 import _clean_rel
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
import re

def _role_from_path(tokens: list[str]) -> str:
    if "test" in tokens or "validation" in tokens:
        return "validation and survival gate"
    if "intent" in tokens:
        return "intent compilation and routing"
    if "sim" in tokens or "simulation" in tokens:
        return "file simulation and grading"
    if "email" in tokens or "memory" in tokens:
        return "file memory and durable conversation"
    if "deepseek" in tokens:
        return "deep rewrite model queue"
    if "manifest" in tokens:
        return "scope constitution and file ownership"
    return "source responsibility inferred from path and history"


def _relationship_type(rel: str, neighbor: str, sources: dict[str, Any]) -> str:
    for edge in (sources.get("council") or {}).get("relationships") or []:
        left = _clean_rel(edge.get("from"))
        right = _clean_rel(edge.get("to"))
        if {left, right} == {rel, neighbor}:
            return str(edge.get("type") or "peer")
    if Path(neighbor).name.startswith("test_"):
        return "validator"
    if neighbor.lower().endswith("manifest.md"):
        return "manifest"
    return "peer_context"


def _vein_reason(relation: str) -> str:
    return {
        "friendship": "load together; prior council says they cooperate",
        "beef": "load together; rewrite order or layout may conflict",
        "validator": "test gate should judge the rewrite",
        "manifest": "scope responsibility must stay explicit",
    }.get(relation, "peer context affects diagnosis")


def _top_growth_tags(growth: list[dict[str, Any]]) -> list[str]:
    counts: Counter[str] = Counter()
    for row in growth:
        counts.update(str(tag) for tag in row.get("growth_tags") or [])
    return [tag for tag, _count in counts.most_common(12)]
