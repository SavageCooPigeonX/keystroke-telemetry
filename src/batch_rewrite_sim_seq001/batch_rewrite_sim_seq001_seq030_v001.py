"""batch_rewrite_sim_seq001_seq030_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq033_v001 import _stem_key
from .batch_rewrite_sim_seq001_seq033_v001 import _tokens
from pathlib import Path
from typing import Any
import os
import re

def _identity_growth(compiled: dict[str, Any], rel: str, validation: dict[str, Any], interlink: float) -> dict[str, Any]:
    stem = Path(rel).stem
    tokens = sorted((_tokens(rel) | set(compiled.get("tokens") or [])))[:16]
    return {
        "file": rel,
        "stem": stem,
        "identity_key": f"{_stem_key(stem)}:{compiled.get('verb', 'route')}:{compiled.get('target', 'work')}",
        "growth_tags": tokens,
        "interlink_score": round(interlink, 3),
        "imports_seen": len(validation.get("imports") or []),
        "referenced_by_seen": len(validation.get("referenced_by") or []),
    }


def _fire_record(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "file_sim_fire/v1",
        "ts": result.get("ts"),
        "trigger": result.get("trigger"),
        "status": result.get("status"),
        "intent_key": (result.get("intent") or {}).get("intent_key", ""),
        "target_state": result.get("target_state"),
        "proposal_count": len(result.get("proposals") or []),
        "top_files": [p.get("path") for p in (result.get("proposals") or [])[:5]],
    }


def _identity_growth_record(result: dict[str, Any], proposal: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "file_identity_growth/v1",
        "ts": result.get("ts"),
        "trigger": result.get("trigger"),
        "intent_key": (result.get("intent") or {}).get("intent_key", ""),
        **(proposal.get("identity_growth") or {}),
    }
