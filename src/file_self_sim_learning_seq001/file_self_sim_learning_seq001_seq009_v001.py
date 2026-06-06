"""file_self_sim_learning_seq001_seq009_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq036_v001 import _candidate_allowed
from .file_self_sim_learning_seq001_seq038_v001 import _clean_rel
from .file_self_sim_learning_seq001_seq038_v001 import _tokens
from .file_self_sim_learning_seq001_seq040_v001 import _add
from pathlib import Path
from typing import Any
import re

def _seed_from_size_pressure(
    root: Path,
    bucket: dict[str, dict[str, Any]],
    sources: dict[str, Any],
    intent_model: dict[str, Any],
    settings: dict[str, Any],
) -> None:
    pressure_terms = {
        "split", "splitting", "cap", "overcap", "over", "large", "monolith",
        "sequence", "architecture", "maintain", "maintenance", "heal", "self",
    }
    tokens = set(intent_model.get("tokens") or [])
    explicit_pressure = bool(tokens & pressure_terms)
    registry = sources.get("architecture_registry") or {}
    files = [
        item for item in registry.get("files", [])
        if isinstance(item, dict) and item.get("split_pressure", 0) > 0
    ]
    for item in files:
        rel = _clean_rel(item.get("file"))
        if not rel or not _candidate_allowed(root, rel):
            continue
        pressure = float(item.get("split_pressure") or 0)
        path_overlap = len(tokens & set(_tokens(rel)))
        if rel in bucket:
            _add(bucket, rel, 0.8 + pressure * 1.2, "size pressure should affect maintenance routing", "size_pressure")
        if explicit_pressure and (path_overlap or item.get("size_state") in {"critical", "warn"}):
            points = 2.2 + min(pressure, 3.0) * 1.4 + path_overlap * 0.8
            _add(bucket, rel, points, "over-cap file woke for split-plan job", "size_pressure")
