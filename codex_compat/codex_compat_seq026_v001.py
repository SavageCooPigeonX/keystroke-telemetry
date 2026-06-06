"""codex_compat_seq026_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_seq002_v001 import _ensure_repo_on_path
from .codex_compat_seq007_v001 import _latest_json
from .codex_compat_seq033_v001 import _load_json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import os
import re

def _bind_intent_loop_edit(root: Path, edit_entry: dict[str, Any]) -> dict[str, Any]:
    try:
        _ensure_repo_on_path(root)
        from src.intent_loop_closer_seq001_v001 import bind_edit_to_latest_loop
        return bind_edit_to_latest_loop(root, edit_entry)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def close_intent_loop(
    root: Path,
    loop_id: str | None = None,
    status: str = "verified",
    note: str = "",
) -> dict[str, Any]:
    try:
        _ensure_repo_on_path(root)
        from src.intent_loop_closer_seq001_v001 import close_intent_loop as _close
        return _close(root, loop_id=loop_id, status=status, note=note)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def get_intent_loop_status(root: Path) -> dict[str, Any]:
    try:
        _ensure_repo_on_path(root)
        from src.intent_loop_closer_seq001_v001 import intent_loop_summary
        return intent_loop_summary(root)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def _parse_iso_ts(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _latest_log_ts(root: Path, rel_path: str) -> tuple[datetime | None, dict[str, Any]]:
    path = root / rel_path
    if rel_path.endswith(".jsonl"):
        row = _latest_json(path) or {}
        return _parse_iso_ts(row.get("ts")), row
    data = _load_json(path) or {}
    return _parse_iso_ts(data.get("ts")), data
