"""analyze_prompt_behavior_compiled_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from .analyze_prompt_behavior_compiled_seq023_v001 import NEGATIVE_PATTERNS
from .analyze_prompt_behavior_compiled_seq023_v001 import POSITIVE_PATTERNS
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import re

def _parse_ts(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except Exception:
        return datetime.fromtimestamp(0, tz=timezone.utc)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"ts": "", "msg": line, "parse_error": True})
    return rows


def _has_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _themes(text: str) -> list[str]:
    return [name for name, pattern in THEMES.items() if re.search(pattern, text, re.IGNORECASE)]


def _reinforcement(row: dict[str, Any], text: str) -> str:
    positive = _has_any(text, POSITIVE_PATTERNS)
    negative = _has_any(text, NEGATIVE_PATTERNS)
    if positive and negative:
        return "mixed"
    if positive:
        return "positive"
    if negative:
        return "negative"
    if row.get("cognitive_state") == "frustrated":
        return "negative_soft"
    return "neutral"
