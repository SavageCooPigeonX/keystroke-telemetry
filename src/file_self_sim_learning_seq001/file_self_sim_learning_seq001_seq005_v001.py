"""file_self_sim_learning_seq001_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq006_v001 import _seed_from_council
from .file_self_sim_learning_seq001_seq006_v001 import _seed_from_memory
from .file_self_sim_learning_seq001_seq006_v001 import _seed_from_prompt_contract_fallback
from .file_self_sim_learning_seq001_seq006_v001 import _seed_from_proposals
from .file_self_sim_learning_seq001_seq007_v001 import _seed_from_dead_pairs
from .file_self_sim_learning_seq001_seq007_v001 import _seed_from_identity_growth
from .file_self_sim_learning_seq001_seq008_v001 import _seed_from_numeric_surface
from .file_self_sim_learning_seq001_seq008_v001 import _seed_from_path_tokens
from .file_self_sim_learning_seq001_seq009_v001 import _seed_from_size_pressure
from .file_self_sim_learning_seq001_seq036_v001 import _candidate_allowed
from .file_self_sim_learning_seq001_seq038_v001 import _clean_rel
from .file_self_sim_learning_seq001_seq039_v001 import _exists_bonus
from .file_self_sim_learning_seq001_seq040_v001 import _dedupe
from .file_self_sim_learning_seq001_seq040_v001 import _source_wake_bonus
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
import re

def _select_candidates(
    root: Path,
    intent_model: dict[str, Any],
    sources: dict[str, Any],
    limit: int,
    settings: dict[str, Any],
) -> list[dict[str, Any]]:
    bucket: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"score": 0.0, "reasons": [], "proposal": {}, "signals": Counter()}
    )
    _seed_from_proposals(bucket, sources)
    _seed_from_council(bucket, sources)
    _seed_from_memory(bucket, sources)
    _seed_from_identity_growth(bucket, sources, intent_model)
    _seed_from_dead_pairs(bucket, sources, intent_model)
    _seed_from_numeric_surface(root, bucket, sources, intent_model)
    _seed_from_path_tokens(root, bucket, intent_model)
    _seed_from_size_pressure(root, bucket, sources, intent_model, settings)
    if not bucket:
        _seed_from_prompt_contract_fallback(root, bucket)
    rows = []
    for rel, data in bucket.items():
        rel = _clean_rel(rel)
        if not rel or not _candidate_allowed(root, rel):
            continue
        data["file"] = rel
        data["score"] = round(float(data["score"]), 4)
        data["signals"] = dict(data["signals"])
        data["reasons"] = _dedupe(data["reasons"])[:8]
        rows.append(data)
    rows.sort(
        key=lambda item: (
            item["score"] + _source_wake_bonus(item["file"]),
            item["score"],
            _exists_bonus(root, item["file"]),
        ),
        reverse=True,
    )
    return rows[: max(limit, 1)]
