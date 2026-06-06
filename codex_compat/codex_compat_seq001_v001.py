"""codex_compat_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import re

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _words(text: str) -> list[str]:
    return [part.strip(".,;:!?()[]{}\"'`") for part in str(text).split() if part.strip(".,;:!?()[]{}\"'`")]


def _parse_deleted_words(deleted_words: list[Any] | None = None, deleted_text: str = "") -> list[str]:
    words: list[str] = []
    for item in deleted_words or []:
        if isinstance(item, dict):
            text = item.get("word") or item.get("text") or item.get("deleted") or item.get("value") or ""
        else:
            text = str(item)
        words.extend(_words(text))
    words.extend(_words(deleted_text))
    seen = set()
    unique = []
    for word in words:
        key = word.lower()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(word)
    return unique[:30]


def _state_from_deletions(deletion_ratio: float, hesitation_count: int = 0) -> str:
    if deletion_ratio > 0.4 or hesitation_count > 5:
        return "frustrated"
    if deletion_ratio > 0.2 or hesitation_count > 2:
        return "hesitant"
    if deletion_ratio > 0:
        return "neutral"
    return "unknown"


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
