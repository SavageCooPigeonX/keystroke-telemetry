"""opus_prompt_box_seq001_v001_compiled_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_prompt_box_seq001_v001_compiled_seq012_v001 import _next_id
from typing import Any
import re

def _intent_routes(intent_graph: dict[str, Any]) -> list[dict[str, Any]]:
    routes = []
    for intent in (intent_graph.get("intents") or [])[:12]:
        if intent.get("void"):
            continue
        routes.append({
            "intent_key": intent.get("intent_key"),
            "domain_id": intent.get("domain_id"),
            "scope": intent.get("scope"),
            "confidence": intent.get("confidence"),
            "files": [score.get("file") for score in intent.get("file_scores") or [] if score.get("file")][:6],
        })
    return routes


def _routing_note(prompt: str, intent_graph: dict[str, Any], open_rows: list[dict[str, Any]]) -> str:
    domains = list(dict.fromkeys(row.get("domain_id") for row in (intent_graph.get("intents") or []) if row.get("domain_id")))[:4]
    top = open_rows[0]["intent_key"] if open_rows else "none"
    if not prompt:
        return "No operator prompt; carrying forward taxed open problems only."
    if domains:
        return (
            f"Prompt routes through domains {', '.join(domains)}. "
            f"Primary open problem `{top}`. Opus selects intent keys, then files, then sim."
        )
    return f"Prompt lacks strong domain manifest match; holding `{top}` as provisional route."


def _problem_from_intent(intent: dict[str, Any], prompt: str, now: str) -> dict[str, Any]:
    files = [row.get("file") for row in intent.get("file_scores") or [] if row.get("file")][:6]
    return {
        "id": _next_id("pb"),
        "title": intent.get("segment") or intent.get("intent_key") or "intent move",
        "intent_key": intent.get("intent_key", ""),
        "scope": intent.get("scope", ""),
        "domain_id": intent.get("domain_id", ""),
        "prompt": prompt[:300],
        "confidence": float(intent.get("confidence") or 0.0),
        "priority_score": min(0.95, 0.35 + float(intent.get("confidence") or 0.0)),
        "focus_files": files,
        "source": "intent_graph",
        "status": "open",
        "writer": "claude-opus",
        "created_ts": now,
        "last_refined_ts": now,
        "prompt_hits": 0,
    }
