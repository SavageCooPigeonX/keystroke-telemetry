"""hush_intent_runtime_seq001_v001_compiled_seq009_v001.py — Auto-extracted by Pigeon Compiler."""
from .hush_intent_runtime_seq001_v001_compiled_seq010_v001 import LOCAL_REPO
from collections import Counter
from pathlib import Path
from typing import Any
import json
import re

def _intent_map(journal: list[dict[str, Any]], semantic: dict[str, Any], moves: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(row.get("intent") or "unknown") for row in journal)
    return {
        "schema": "hush_persistent_intent_map/v1",
        "recent_prompt_count": len(journal),
        "recent_intents": dict(counts),
        "semantic_intents": semantic.get("semantic_intents") or ([semantic.get("semantic_intent")] if semantic.get("semantic_intent") else []),
        "active_threads": [move["name"] for move in moves],
    }


def _repo_room_context(root: Path, repo: dict[str, Any]) -> dict[str, Any]:
    active = repo.get("active_repo")
    if active and active not in {LOCAL_REPO, "ambiguous"}:
        data = _json(root / "logs" / f"repo_fingerprint_{active}.json")
        return {
            "repo": active,
            "privacy": data.get("privacy", "closed"),
            "files_indexed": data.get("files_indexed", 0),
            "callable_context": [row.get("identity") for row in (data.get("files") or [])[:8]],
        }
    return {"repo": active, "privacy": "local", "callable_context": []}


def _recent_outcome(outcome: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": outcome.get("status") or outcome.get("decision") or "",
        "reason": _snip(outcome.get("reason") or outcome.get("summary") or "", 220),
    }


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z][A-Za-z0-9_]{1,}", str(text or ""))]


def _snip(text: Any, limit: int) -> str:
    one = " ".join(str(text or "").split())
    return one if len(one) <= limit else one[: max(0, limit - 3)].rstrip() + "..."


def _json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace")) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}
