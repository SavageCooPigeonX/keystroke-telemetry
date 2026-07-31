"""opus_prompt_box_seq001_v001_compiled_seq010_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_prompt_box_seq001_v001_compiled_seq012_v001 import _next_id
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import DONE_STATUSES
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import DROP_STATUS
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import _load_json
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import _now
from pathlib import Path
from typing import Any
import json
import re

def _absorb_legacy_tasks(root: Path) -> list[dict[str, Any]]:
    data = _load_json(root / "task_queue.json") or {}
    tasks = data.get("tasks") if isinstance(data, dict) else []
    rows = []
    for task in tasks or []:
        if not isinstance(task, dict):
            continue
        status = str(task.get("status") or "open")
        if status in DONE_STATUSES:
            mapped = "done"
        elif status == DROP_STATUS:
            mapped = DROP_STATUS
        else:
            mapped = "open"
        rows.append({
            "id": task.get("id") or _next_id("pb"),
            "title": task.get("title") or task.get("intent") or "legacy task",
            "intent_key": task.get("intent_key", ""),
            "scope": task.get("scope", ""),
            "prompt": task.get("intent", ""),
            "confidence": float(task.get("confidence") or 0.0),
            "priority_score": _legacy_priority(task),
            "focus_files": list(task.get("focus_files") or []),
            "source": task.get("source") or "legacy_task_queue",
            "status": mapped,
            "writer": "claude-opus",
            "created_ts": task.get("created_ts") or _now(),
            "last_refined_ts": task.get("last_refined_ts") or task.get("created_ts") or _now(),
            "prompt_hits": int(task.get("prompt_hits") or 0),
        })
    return rows


def _legacy_priority(task: dict[str, Any]) -> float:
    table = {"high": 0.75, "medium": 0.5, "low": 0.3, "needs_clarity": 0.2}
    return table.get(str(task.get("priority") or ""), 0.45)


def _bug_candidates(root: Path) -> list[dict[str, Any]]:
    try:
        from src.file_bug_surface_seq001_v001 import build_file_bug_surface

        surface = build_file_bug_surface(root, write=False)
        return list(surface.get("bugs") or [])[:12]
    except Exception:
        surface = _load_json(root / "logs/file_bug_surface_latest.json") or {}
        return list(surface.get("bugs") or [])[:12]
