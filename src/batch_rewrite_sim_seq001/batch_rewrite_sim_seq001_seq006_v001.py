"""batch_rewrite_sim_seq001_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq007_v001 import _job_role
from .batch_rewrite_sim_seq001_seq007_v001 import _member_mood
from .batch_rewrite_sim_seq001_seq007_v001 import _model_grievance
from .batch_rewrite_sim_seq001_seq008_v001 import _dedupe_strings
from .batch_rewrite_sim_seq001_seq008_v001 import _proposal_token_estimate
from pathlib import Path
from typing import Any
import os
import re

def _job_council_member(root: Path, proposal: dict[str, Any], index: int) -> dict[str, Any]:
    rel = str(proposal.get("path") or "unknown").replace("\\", "/")
    validation = proposal.get("cross_file_validation") or {}
    context_files = _dedupe_strings(str(item).replace("\\", "/") for item in (proposal.get("context_injection") or []))
    friendships = [
        item for item in context_files
        if item != rel and not item.lower().endswith("manifest.md")
    ]
    refs = [
        str(item).replace("\\", "/")
        for item in (validation.get("referenced_by") or [])
        if item and str(item).replace("\\", "/") != rel
    ]
    friendships = _dedupe_strings([*friendships, *refs])[:8]
    beefs = _dedupe_strings(
        str(item.get("with") or "").replace("\\", "/")
        for item in (proposal.get("incompatibilities") or [])
        if isinstance(item, dict) and item.get("with")
    )
    checks = (proposal.get("ten_q") or {}).get("checks") or []
    failed = [item for item in checks if isinstance(item, dict) and not item.get("passed")]
    passed = [item for item in checks if isinstance(item, dict) and item.get("passed")]
    return {
        "file": rel,
        "scope": Path(rel).parent.as_posix() or "root",
        "role": _job_role(index, rel, proposal, failed, friendships),
        "approx_tokens": _proposal_token_estimate(root, proposal),
        "interlink_score": proposal.get("interlink_score", 0),
        "confidence": proposal.get("confidence", 0),
        "decision": proposal.get("decision", ""),
        "context_files": context_files,
        "friendships": friendships,
        "beefs": beefs,
        "passed_checks": len(passed),
        "failed_checks": len(failed),
        "failed_check_keys": [str(item.get("key", "unknown")) for item in failed[:8]],
        "accumulated_sims": sum(int(value) for value in (proposal.get("event_counts") or {}).values()),
        "mood": _member_mood(rel, failed, friendships, beefs),
        "model_grievance": _model_grievance(proposal, failed),
    }
