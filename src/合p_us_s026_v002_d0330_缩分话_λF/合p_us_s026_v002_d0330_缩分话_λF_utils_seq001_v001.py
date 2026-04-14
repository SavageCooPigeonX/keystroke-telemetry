"""合p_us_s026_v002_d0330_缩分话_λF_utils_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 39 lines | ~309 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

def _parse_ts(ts_val: Any) -> float:
    """Convert any timestamp format to epoch ms."""
    if isinstance(ts_val, (int, float)):
        # Already epoch ms if > 1e12, epoch seconds if < 1e12
        return ts_val if ts_val > 1e12 else ts_val * 1000
    if isinstance(ts_val, str):
        try:
            dt = datetime.fromisoformat(ts_val)
            return dt.timestamp() * 1000
        except (ValueError, TypeError):
            return 0.0
    return 0.0


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").strip().splitlines():
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def _load_json(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    return data.get("entries", data.get("events", []))
