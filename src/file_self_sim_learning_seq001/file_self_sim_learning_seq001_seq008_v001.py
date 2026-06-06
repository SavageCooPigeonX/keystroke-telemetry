"""file_self_sim_learning_seq001_seq008_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq035_v001 import _numeric_predictions
from .file_self_sim_learning_seq001_seq036_v001 import _scan_repo_files
from .file_self_sim_learning_seq001_seq038_v001 import _clean_rel
from .file_self_sim_learning_seq001_seq038_v001 import _tokens
from .file_self_sim_learning_seq001_seq040_v001 import _add
from pathlib import Path
from typing import Any
import re

def _seed_from_numeric_surface(
    root: Path,
    bucket: dict[str, dict[str, Any]],
    sources: dict[str, Any],
    intent_model: dict[str, Any],
) -> None:
    for item in _numeric_predictions(root, intent_model, sources)[:16]:
        rel = _clean_rel(item.get("file"))
        if rel:
            _add(bucket, rel, 1.5 + float(item.get("score") or 0) * 4.0, "numeric prompt encoding selected file", "numeric")


def _seed_from_path_tokens(root: Path, bucket: dict[str, dict[str, Any]], intent_model: dict[str, Any]) -> None:
    prompt_tokens = set(intent_model.get("tokens") or [])
    if not prompt_tokens:
        return
    for rel in _scan_repo_files(root):
        overlap = prompt_tokens & set(_tokens(rel))
        if len(overlap) >= 2:
            points = 2.0 + len(overlap) * 1.1
            if len(overlap) >= 3:
                points += 4.0
            _add(bucket, rel, points, "path tokens match current intent", "path")
