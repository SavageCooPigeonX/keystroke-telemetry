"""batch_rewrite_sim_seq001_seq015_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq016_v001 import _overwrite_path
from .batch_rewrite_sim_seq001_seq017_v001 import _reasoning_budget
from .batch_rewrite_sim_seq001_seq028_v001 import _cross_file_validation
from .batch_rewrite_sim_seq001_seq028_v001 import _metadata_candidate
from .batch_rewrite_sim_seq001_seq028_v001 import _resolve_alias_targets
from .batch_rewrite_sim_seq001_seq028_v001 import _source_candidate
from .batch_rewrite_sim_seq001_seq029_v001 import _context_injection
from .batch_rewrite_sim_seq001_seq029_v001 import _proposed_fix
from .batch_rewrite_sim_seq001_seq029_v001 import _validation_plan
from .batch_rewrite_sim_seq001_seq030_v001 import _identity_growth
from .batch_rewrite_sim_seq001_seq031_v001 import _interlink_score
from .batch_rewrite_sim_seq001_seq033_v001 import _stem_key
from .batch_rewrite_sim_seq001_seq034_v001 import RISKY_BITS
from .batch_rewrite_sim_seq001_seq034_v001 import RISKY_SUFFIXES
from pathlib import Path
from typing import Any
import os
import re

def _proposal(
    root: Path,
    rel: str,
    data: dict[str, Any],
    compiled: dict[str, Any],
    failure: dict[str, Any],
    dirty: set[str],
    config: dict[str, Any],
) -> dict[str, Any]:
    alias_targets = _resolve_alias_targets(root, rel)
    alias_from = ""
    if alias_targets and alias_targets[0] != str(rel).replace("\\", "/"):
        alias_from = str(rel).replace("\\", "/")
        rel = alias_targets[0]
        data.setdefault("evidence", []).append(f"identity_alias:{alias_from}")
    path = root / rel
    validation = _cross_file_validation(root, rel, dirty)
    stem = _stem_key(rel)
    chronic = stem in set(failure.get("persistent_modules", []))
    risky_path = rel.replace("\\", "/")
    risk = 0.12
    risk += 0.22 if _metadata_candidate(rel, set(compiled.get("tokens") or [])) else 0
    risk += 0.34 if not _source_candidate(rel) else 0
    risk += 0.28 if not path.exists() else 0
    risk += 0.18 if rel in dirty else 0
    risk += 0.18 if path.suffix.lower() in RISKY_SUFFIXES else 0
    risk += 0.18 if any(bit in risky_path for bit in RISKY_BITS) else 0
    risk += 0.14 if validation.get("line_count", 0) > 400 else 0
    risk += 0.12 if chronic else 0
    interlink = _interlink_score(rel, validation, compiled)
    reward = min(1.0, 0.18 + data["score"] / 6 + min(sum(data["events"].values()), 20) / 40 + interlink * 0.22)
    confidence = max(0.0, min(1.0, reward * (1.0 - min(risk, 0.95))))
    decision = "safe_dry_run" if confidence >= 0.35 and risk < 0.45 else "needs_review"
    if risk >= 0.72 or not path.exists():
        decision = "blocked"
    return {
        "path": rel,
        "rewrite_target_type": "source" if _source_candidate(rel) else "context_memory",
        "target_state": config.get("target_state", "interlinked_source_state"),
        "interlink_score": round(interlink, 3),
        "decision": decision,
        "approval_gate": "operator_required",
        "overwrite_path": _overwrite_path(decision, rel),
        "reasoning_budget": _reasoning_budget(decision),
        "reward": round(reward, 3),
        "risk": round(min(risk, 1.0), 3),
        "confidence": round(confidence, 3),
        "event_counts": dict(data["events"]),
        "evidence": data["evidence"][:5],
        "failure_memory": {"chronic_or_eternal": chronic},
        "identity_alias": {"from": alias_from, "resolved": rel} if alias_from else {},
        "identity_growth": _identity_growth(compiled, rel, validation, interlink),
        "proposed_fix": _proposed_fix(compiled, rel, decision),
        "context_injection": _context_injection(compiled, rel, validation),
        "validation_plan": _validation_plan(rel, validation),
        "incompatibilities": [],
        "cross_file_validation": validation,
    }
