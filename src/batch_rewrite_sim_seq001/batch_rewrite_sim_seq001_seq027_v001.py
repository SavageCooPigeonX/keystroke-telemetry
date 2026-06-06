"""batch_rewrite_sim_seq001_seq027_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq026_v001 import _add_candidate
from .batch_rewrite_sim_seq001_seq028_v001 import _metadata_candidate
from .batch_rewrite_sim_seq001_seq028_v001 import _resolve_alias_targets
from .batch_rewrite_sim_seq001_seq028_v001 import _source_candidate
from .batch_rewrite_sim_seq001_seq033_v001 import _tokens
from pathlib import Path
from typing import Any
import re

def _add_candidate_with_aliases(
    root: Path,
    bucket: dict[str, dict[str, Any]],
    path: str,
    points: float,
    reason: str,
) -> None:
    targets = _resolve_alias_targets(root, path)
    if not targets:
        _add_candidate(bucket, path, points, reason)
        return
    for target in targets:
        alias_reason = reason if target == str(path).replace("\\", "/") else f"identity_alias:{reason}"
        _add_candidate(bucket, target, points, alias_reason)


def _history_points(pair: dict[str, Any], tokens: set[str], scope: str) -> float:
    path = str(pair.get("new_path") or pair.get("old_path") or "").replace("\\", "/")
    text = " ".join([path, str(pair.get("intent_key", "")), str(pair.get("subject", ""))])
    hits = len(tokens & _tokens(text))
    points = hits / max(len(tokens), 4)
    if scope and scope != "root" and "/" in scope and path.startswith(scope):
        points += 0.7
    if pair.get("event_type") in {"patch", "rename"}:
        points += 0.08
    return points if points >= 0.18 else 0.0


def _candidate_sort_score(root: Path, path: str, data: dict[str, Any], tokens: set[str]) -> float:
    score = float(data["score"])
    if _source_candidate(path):
        score += 1.4
    else:
        score -= 4.0
    if _metadata_candidate(path, tokens):
        score -= 1.8
    if not (root / path).exists():
        score -= 6.0
    return score
