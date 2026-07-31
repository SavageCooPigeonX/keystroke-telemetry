"""opus_prompt_box_seq001_v001_compiled_seq009_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_prompt_box_seq001_v001_compiled_seq012_v001 import _next_id
from .opus_prompt_box_seq001_v001_compiled_seq012_v001 import _slug
from typing import Any
import re

def _problem_from_prompt(prompt: str, intent_graph: dict[str, Any], now: str) -> dict[str, Any]:
    intent = ((intent_graph.get("intents") or [{}])[0]) if intent_graph.get("intents") else {}
    return {
        "id": _next_id("pb"),
        "title": prompt[:120],
        "intent_key": intent.get("intent_key") or f"root:route:{_slug(prompt)}:read",
        "scope": intent.get("scope") or "root",
        "prompt": prompt[:300],
        "confidence": float(intent.get("confidence") or 0.2),
        "priority_score": 0.3,
        "focus_files": [],
        "source": "operator_prompt",
        "status": "open",
        "writer": "claude-opus",
        "created_ts": now,
        "last_refined_ts": now,
        "prompt_hits": 1,
    }
