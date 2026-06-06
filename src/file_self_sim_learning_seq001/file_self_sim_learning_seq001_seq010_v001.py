"""file_self_sim_learning_seq001_seq010_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq023_v001 import _context_veins
from .file_self_sim_learning_seq001_seq023_v001 import _responsibility_profile
from .file_self_sim_learning_seq001_seq024_v001 import _node_relationship_weight
from .file_self_sim_learning_seq001_seq024_v001 import _size_pressure
from .file_self_sim_learning_seq001_seq024_v001 import _validation_confidence
from .file_self_sim_learning_seq001_seq029_v001 import _learned_enough
from .file_self_sim_learning_seq001_seq030_v001 import _growth_for_file
from .file_self_sim_learning_seq001_seq030_v001 import _memory_for_file
from .file_self_sim_learning_seq001_seq030_v001 import _profile_for_file
from .file_self_sim_learning_seq001_seq031_v001 import _neighbors_for_file
from .file_self_sim_learning_seq001_seq033_v001 import _next_question
from .file_self_sim_learning_seq001_seq033_v001 import _wake_role
from .file_self_sim_learning_seq001_seq034_v001 import _nearest_manifest
from .file_self_sim_learning_seq001_seq034_v001 import _tests_for_file
from .file_self_sim_learning_seq001_seq038_v001 import _hash_encoding
from .file_self_sim_learning_seq001_seq039_v001 import _estimate_tokens
from pathlib import Path
from typing import Any
import json
import re

def _wake_node(
    root: Path,
    row: dict[str, Any],
    index: int,
    intent_model: dict[str, Any],
    sources: dict[str, Any],
    settings: dict[str, Any],
) -> dict[str, Any]:
    rel = row["file"]
    proposal = row.get("proposal") or {}
    memory = _memory_for_file(root, rel, sources)
    profile = _profile_for_file(rel, sources)
    growth = _growth_for_file(rel, sources)
    neighbors = _neighbors_for_file(root, rel, proposal, sources)
    tests = _tests_for_file(root, rel, proposal)
    learned = _learned_enough(memory, profile, growth, proposal, tests)
    role = _wake_role(index, rel, proposal, neighbors, tests)
    size_pressure = _size_pressure(root, rel, settings)
    validation_confidence = _validation_confidence(tests, proposal)
    relationship_weight = _node_relationship_weight(rel, neighbors, sources)
    basis = json.dumps({
        "intent": intent_model.get("intent_key"),
        "file": rel,
        "memory": memory.get("summary", ""),
        "neighbors": neighbors[:8],
        "tests": tests[:5],
        "size_pressure": size_pressure.get("state"),
        "validation_confidence": validation_confidence,
        "relationship_weight": relationship_weight,
    }, sort_keys=True)
    return {
        "sequence": index + 1,
        "file": rel,
        "role": role,
        "wake_score": row["score"],
        "wake_reason": "; ".join(row.get("reasons") or [])[:240],
        "signals": row.get("signals", {}),
        "numeric_encoding": _hash_encoding(basis),
        "responsibility_profile": _responsibility_profile(root, rel, memory, profile, growth),
        "known_neighbors": neighbors[:12],
        "context_veins": _context_veins(rel, neighbors, sources),
        "manifest": _nearest_manifest(root, rel),
        "tests": tests[:8],
        "estimated_tokens": _estimate_tokens(root, rel),
        "size_pressure": size_pressure,
        "validation_confidence": validation_confidence,
        "relationship_weight": relationship_weight,
        "learned_enough": learned,
        "next_question": _next_question(role, learned, neighbors, tests),
    }
