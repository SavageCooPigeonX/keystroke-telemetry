"""opus_prompt_box_seq001_v001_compiled_seq008_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_prompt_box_seq001_v001_compiled_seq012_v001 import _next_id
from .opus_prompt_box_seq001_v001_compiled_seq012_v001 import _slug
from typing import Any
import re

def _problem_from_bug(bug: dict[str, Any], now: str) -> dict[str, Any]:
    owner = str(bug.get("owner") or "repo")
    title = str(bug.get("title") or "pipeline bug")
    sev = str(bug.get("severity") or "P2").lower()
    intent_key = f"{_slug(owner)}:repair:{_slug(title)}:{sev}"
    return {
        "id": _next_id("pb"),
        "title": title,
        "intent_key": intent_key,
        "scope": owner.split("/")[0] if "/" in owner else "root",
        "domain_id": "project.keystroke_telemetry",
        "prompt": "",
        "confidence": 0.55 if sev.startswith("p0") else 0.4,
        "priority_score": 0.7 if sev.startswith("p0") else 0.45,
        "focus_files": [owner] if owner.endswith(".py") or "/" in owner else [],
        "source": bug.get("source") or "file_bug_surface",
        "status": "open",
        "writer": "claude-opus",
        "created_ts": now,
        "last_refined_ts": now,
        "prompt_hits": 0,
        "bug_id": bug.get("bug_id"),
    }


def _problem_from_candidate(cand: dict[str, Any], now: str) -> dict[str, Any]:
    return {
        "id": _next_id("pb"),
        "title": cand.get("intent_key") or cand.get("prompt") or "candidate",
        "intent_key": cand.get("intent_key", ""),
        "scope": cand.get("scope", ""),
        "prompt": cand.get("prompt", ""),
        "confidence": float(cand.get("confidence") or 0.0),
        "priority_score": min(0.9, 0.25 + float(cand.get("confidence") or 0.0)),
        "focus_files": [cand.get("manifest_path")] if cand.get("manifest_path") else [],
        "source": cand.get("source") or "candidate",
        "status": "open",
        "writer": "claude-opus",
        "created_ts": now,
        "last_refined_ts": now,
        "prompt_hits": 0,
        "kind": cand.get("kind"),
    }
