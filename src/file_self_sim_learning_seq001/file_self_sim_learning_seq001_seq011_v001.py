"""file_self_sim_learning_seq001_seq011_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq023_v001 import _accumulated_knowledge
from .file_self_sim_learning_seq001_seq023_v001 import _backward_targets
from .file_self_sim_learning_seq001_seq025_v001 import _split_plan_request
from .file_self_sim_learning_seq001_seq028_v001 import _deepseek_learning_instruction
from .file_self_sim_learning_seq001_seq029_v001 import _overwrite_readiness
from .file_self_sim_learning_seq001_seq032_v001 import _proposal_for_file
from .file_self_sim_learning_seq001_seq033_v001 import _default_validation
from .file_self_sim_learning_seq001_seq041_v001 import PACKET_SCHEMA
from pathlib import Path
from typing import Any
import hashlib
import json
import re

def _learning_packet(
    root: Path,
    node: dict[str, Any],
    intent_model: dict[str, Any],
    sources: dict[str, Any],
    settings: dict[str, Any],
) -> dict[str, Any]:
    rel = node["file"]
    proposal = ((sources.get("latest") or {}).get("proposals_by_file") or {}).get(rel) or {}
    if not proposal:
        proposal = _proposal_for_file(rel, sources)
    packet_seed = json.dumps({
        "intent": intent_model.get("intent_key"),
        "file": rel,
        "encoding": node.get("numeric_encoding", {}).get("signature"),
    }, sort_keys=True)
    packet_id = "dslp-" + hashlib.sha256(packet_seed.encode("utf-8")).hexdigest()[:16]
    validation = proposal.get("cross_file_validation") or {}
    validation_plan = proposal.get("validation_plan") or _default_validation(root, rel, node.get("tests") or [])
    readiness = _overwrite_readiness(node, proposal, settings)
    return {
        "schema": PACKET_SCHEMA,
        "packet_id": packet_id,
        "file": rel,
        "intent_key": intent_model.get("intent_key", ""),
        "mode": settings["mode"],
        "target_state": settings["target_state"],
        "wake_role": node.get("role"),
        "numeric_encoding": node.get("numeric_encoding"),
        "responsibility_profile": node.get("responsibility_profile"),
        "intent_profile": {
            "tokens": intent_model.get("tokens", [])[:32],
            "selected_by": node.get("signals", {}),
            "wake_score": node.get("wake_score", 0),
            "current_question": node.get("next_question"),
        },
        "accumulated_knowledge": _accumulated_knowledge(rel, sources),
        "context_veins": node.get("context_veins", []),
        "size_pressure": node.get("size_pressure", {}),
        "validation_confidence": node.get("validation_confidence", 0),
        "relationship_weight": node.get("relationship_weight", 0),
        "verification_packet": {
            "validation_plan": validation_plan,
            "tests": node.get("tests", []),
            "imports_seen": validation.get("imports", []),
            "referenced_by": validation.get("referenced_by", []),
            "dirty": validation.get("dirty", False),
        },
        "overwrite_readiness": readiness,
        "split_plan_request": _split_plan_request(root, rel, node, validation_plan, settings),
        "deepseek_instruction": _deepseek_learning_instruction(rel, intent_model, node, validation_plan, readiness),
        "backward_learning_targets": _backward_targets(rel, node),
    }
