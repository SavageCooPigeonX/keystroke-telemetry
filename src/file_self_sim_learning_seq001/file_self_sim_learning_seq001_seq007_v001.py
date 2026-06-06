"""file_self_sim_learning_seq001_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq038_v001 import _clean_rel
from .file_self_sim_learning_seq001_seq038_v001 import _tokens
from .file_self_sim_learning_seq001_seq040_v001 import _add
from typing import Any
import re

def _seed_from_identity_growth(
    bucket: dict[str, dict[str, Any]],
    sources: dict[str, Any],
    intent_model: dict[str, Any],
) -> None:
    prompt_tokens = set(intent_model.get("tokens") or [])
    best_by_file: dict[str, float] = {}
    for row in (sources.get("identity_growth") or [])[-120:]:
        rel = _clean_rel(row.get("file"))
        if not rel:
            continue
        growth_tags = set(str(tag) for tag in row.get("growth_tags") or [])
        overlap = len(prompt_tokens & growth_tags)
        path_overlap = len(prompt_tokens & set(_tokens(rel)))
        points = 0.8 + overlap * 0.18 + float(row.get("interlink_score") or 0) * 1.3
        if path_overlap:
            points += path_overlap * 0.6
        else:
            points *= 0.35
        best_by_file[rel] = max(best_by_file.get(rel, 0.0), points)
    for rel, points in best_by_file.items():
        _add(bucket, rel, points, "identity growth remembers similar intent tags", "identity_growth")


def _seed_from_dead_pairs(
    bucket: dict[str, dict[str, Any]],
    sources: dict[str, Any],
    intent_model: dict[str, Any],
) -> None:
    prompt_tokens = set(intent_model.get("tokens") or [])
    for row in (sources.get("dead_pairs") or [])[-160:]:
        rel = _clean_rel(row.get("new_path") or row.get("old_path"))
        if not rel:
            continue
        text = " ".join(str(row.get(key) or "") for key in ("subject", "prompt", "intent_key"))
        overlap = len(prompt_tokens & set(_tokens(text)))
        if overlap or rel in bucket:
            _add(bucket, rel, 0.5 + overlap * 0.25, "rename/change history predicts this file", "history")
