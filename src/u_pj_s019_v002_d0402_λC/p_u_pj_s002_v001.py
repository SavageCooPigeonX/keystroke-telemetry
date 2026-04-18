"""u_pj_s019_v002_d0402_λC_utils_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
import json
import re

def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        entries = []
        with open(path, encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        return entries
    except Exception:
        return []


def _load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text('utf-8'))
    except Exception:
        return None


def _parse_timestamp_ms(value) -> int | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.isdigit():
            return int(text)
        try:
            dt = datetime.fromisoformat(text.replace('Z', '+00:00'))
            return int(dt.timestamp() * 1000)
        except ValueError:
            return None
    return None


def _trim_text(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: max(limit - 3, 0)] + '...'
