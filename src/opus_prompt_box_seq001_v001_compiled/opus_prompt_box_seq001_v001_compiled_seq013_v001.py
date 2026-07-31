"""opus_prompt_box_seq001_v001_compiled_seq013_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import re

def _parse_ts(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

SCHEMA = "opus_prompt_box/v1"

MAX_OPEN_PROBLEMS = 20

TAX_HALF_LIFE_HOURS = 72.0

CANDIDATES_LOG = "logs/prompt_box_candidates.jsonl"

LATEST_JSON = "logs/opus_prompt_box_latest.json"

LATEST_MD = "logs/copilot_prompt_box_latest.md"

HISTORY_JSONL = "logs/opus_prompt_box.jsonl"


OPEN_STATUSES = {"open", "pending", "in_progress"}

DONE_STATUSES = {"done", "verified", "resolved", "closed"}

DROP_STATUS = "tax_dropped"
