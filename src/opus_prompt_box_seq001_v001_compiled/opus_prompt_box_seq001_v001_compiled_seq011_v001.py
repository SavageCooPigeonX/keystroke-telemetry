"""opus_prompt_box_seq001_v001_compiled_seq011_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_prompt_box_seq001_v001_compiled_seq012_v001 import _score_priority
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import _load_json
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import _now
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import _write_json
from pathlib import Path
from typing import Any
import json
import re

def _intent_graph(root: Path, prompt: str) -> dict[str, Any]:
    if not prompt:
        cached = _load_json(root / "logs/intent_graph_latest.json")
        return cached if isinstance(cached, dict) else {}
    try:
        from src.tc_intent_keys_seq001_v001 import generate_intent_graph

        return generate_intent_graph(root, prompt, write=True)
    except Exception as exc:
        return {"schema": "intent_graph_error/v1", "error": str(exc), "intents": []}


def _write_task_queue(root: Path, rows: list[dict[str, Any]]) -> None:
    tasks = []
    for row in rows:
        tasks.append({
            "id": row.get("id"),
            "status": row.get("status"),
            "created_ts": row.get("created_ts"),
            "last_refined_ts": row.get("last_refined_ts"),
            "completed_ts": row.get("completed_ts"),
            "title": row.get("title"),
            "intent": row.get("prompt", "")[:300],
            "intent_key": row.get("intent_key"),
            "scope": row.get("scope"),
            "stage": "opus_prompt_box",
            "priority": _score_priority(row.get("priority_score")),
            "confidence": row.get("confidence"),
            "priority_score": row.get("priority_score"),
            "effective_score": row.get("effective_score"),
            "tax_factor": row.get("tax_factor"),
            "prompt_hits": row.get("prompt_hits"),
            "focus_files": row.get("focus_files") or [],
            "source": "opus_orchestrator",
            "writer": "claude-opus",
            "domain_id": row.get("domain_id"),
            "drop_reason": row.get("drop_reason"),
            "verification_state": "refined" if row.get("status") == "open" else row.get("status"),
        })
    _write_json(root / "task_queue.json", {"tasks": tasks, "writer": "claude-opus", "ts": _now()})
