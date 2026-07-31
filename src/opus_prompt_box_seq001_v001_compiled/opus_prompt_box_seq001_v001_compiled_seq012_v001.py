"""opus_prompt_box_seq001_v001_compiled_seq012_v001.py — Auto-extracted by Pigeon Compiler."""
from .opus_prompt_box_seq001_v001_compiled_seq013_v001 import CANDIDATES_LOG
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import re

def _score_priority(score: Any) -> str:
    value = float(score or 0)
    if value >= 0.7:
        return "high"
    if value >= 0.45:
        return "medium"
    return "low"


def _truncate_candidates(root: Path) -> None:
    path = root / CANDIDATES_LOG
    if not path.exists():
        return
    path.write_text("", encoding="utf-8")


def _load_candidates(root: Path) -> list[dict[str, Any]]:
    path = root / CANDIDATES_LOG
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _problem_key(row: dict[str, Any]) -> str:
    return str(row.get("intent_key") or row.get("id") or row.get("title") or "")


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9_]+", str(text).lower()) if len(t) > 2}


def _slug(text: str) -> str:
    words = _tokens(text)
    return "_".join(sorted(words)[:4])[:48] or "work"


def _latest_prompt(root: Path) -> str:
    path = root / "logs/prompt_journal.jsonl"
    if not path.exists():
        return ""
    for line in reversed(path.read_text(encoding="utf-8", errors="replace").splitlines()):
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        return str(row.get("msg") or row.get("prompt") or "")
    return ""


def _next_id(prefix: str) -> str:
    return f"{prefix}-{int(datetime.now(timezone.utc).timestamp())}"
