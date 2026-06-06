"""file_self_sim_learning_seq001_seq023_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq030_v001 import _growth_for_file
from .file_self_sim_learning_seq001_seq030_v001 import _memory_for_file
from .file_self_sim_learning_seq001_seq030_v001 import _profile_for_file
from .file_self_sim_learning_seq001_seq031_v001 import _history_count_for_file
from .file_self_sim_learning_seq001_seq037_v001 import _relationship_type
from .file_self_sim_learning_seq001_seq037_v001 import _role_from_path
from .file_self_sim_learning_seq001_seq037_v001 import _top_growth_tags
from .file_self_sim_learning_seq001_seq037_v001 import _vein_reason
from .file_self_sim_learning_seq001_seq038_v001 import _tokens
from .file_self_sim_learning_seq001_seq039_v001 import _line_count
from .file_self_sim_learning_seq001_seq039_v001 import _stem_key
from pathlib import Path
from typing import Any
import re

def _responsibility_profile(
    root: Path,
    rel: str,
    memory: dict[str, Any],
    profile: dict[str, Any],
    growth: list[dict[str, Any]],
) -> dict[str, Any]:
    path_tokens = [token for token in _tokens(rel) if token not in {"src", "test", "seq", "v001"}]
    return {
        "file": rel,
        "stem": _stem_key(rel),
        "declared_role": _role_from_path(path_tokens),
        "path_terms": path_tokens[:12],
        "line_count": _line_count(root, rel),
        "memory_summary": memory.get("summary", "no durable memory yet"),
        "profile_hint": profile.get("self_repair_hint", ""),
        "growth_tags": _top_growth_tags(growth),
    }


def _accumulated_knowledge(rel: str, sources: dict[str, Any]) -> dict[str, Any]:
    memory = _memory_for_file(Path("."), rel, sources, allow_read=False)
    profile = _profile_for_file(rel, sources)
    growth = _growth_for_file(rel, sources)
    return {
        "mail_memory": memory,
        "profile_keys": sorted(profile.keys())[:12],
        "recent_identity_growth": growth[-5:],
        "history_events": _history_count_for_file(rel, sources),
    }


def _context_veins(rel: str, neighbors: list[str], sources: dict[str, Any]) -> list[dict[str, str]]:
    veins = []
    for neighbor in neighbors:
        if neighbor == rel:
            continue
        relation = _relationship_type(rel, neighbor, sources)
        veins.append({"file": neighbor, "relation": relation, "reason": _vein_reason(relation)})
    return veins[:10]


def _backward_targets(rel: str, node: dict[str, Any]) -> list[dict[str, str]]:
    targets = [{"file": rel, "learn": "record direct reward and rewrite outcome"}]
    for neighbor in (node.get("known_neighbors") or [])[:6]:
        targets.append({"file": neighbor, "learn": "record sibling compatibility effect"})
    for test in (node.get("tests") or [])[:4]:
        targets.append({"file": test, "learn": "record validation effect"})
    return targets
