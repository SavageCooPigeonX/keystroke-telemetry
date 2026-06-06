"""batch_rewrite_sim_seq001_seq029_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq028_v001 import _source_candidate
from pathlib import Path
from typing import Any
import json
import os
import re

def _validation_plan(rel: str, validation: dict[str, Any]) -> list[str]:
    path = rel.replace("\\", "/")
    if not validation.get("exists"):
        return ["hold: target missing"]
    if path.endswith(".py"):
        stem = Path(path).stem
        return [f"py -m py_compile {path}", f"py -m pytest test_{stem}.py", "git diff --check"]
    if path.endswith(".json"):
        return [f"py -m json.tool {path}", "git diff --check"]
    return ["git diff --check", "manual context review"]


def _context_injection(compiled: dict[str, Any], rel: str, validation: dict[str, Any]) -> list[str]:
    files = [rel]
    manifest = compiled.get("manifest_path")
    if manifest:
        files.append(str(manifest))
    files.extend(validation.get("referenced_by", [])[:4])
    return list(dict.fromkeys(files))


def _proposed_fix(compiled: dict[str, Any], rel: str, decision: str) -> str:
    verb = compiled.get("verb")
    if decision == "blocked":
        return "hold; request operator context before rewrite"
    if _source_candidate(rel):
        return f"source rewrite {rel} toward interlinked state: intent hooks, context edges, validation surfaces"
    if verb == "refactor":
        return f"dry-run structural rewrite plan for {rel}; no source write"
    if verb == "validate":
        return f"compile and cross-file validate {rel} before patch proposal"
    return f"minimal targeted patch proposal for {rel}"


def _distributed_intent_encoding(context_selection: dict[str, Any] | None, compiled: dict[str, Any]) -> dict[str, Any]:
    context_selection = context_selection if isinstance(context_selection, dict) else {}
    files = []
    for item in (context_selection.get("files") or [])[:12]:
        if isinstance(item, dict):
            files.append({"name": item.get("name"), "score": item.get("score", 0)})
    return {
        "intent_key": compiled.get("intent_key", ""),
        "context_confidence": context_selection.get("confidence", 0),
        "context_status": context_selection.get("status", "unknown"),
        "file_votes": files,
        "stale_blocks": context_selection.get("stale_blocks", []),
    }
