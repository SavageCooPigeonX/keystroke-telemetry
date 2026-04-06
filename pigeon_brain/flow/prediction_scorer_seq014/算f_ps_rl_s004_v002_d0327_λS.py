"""prediction_scorer_seq014_reality_loaders_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

from pathlib import Path
from typing import Any
import json
import re

def _load_edit_pairs(root: Path) -> list[dict[str, Any]]:
    """Load all edit pairs (prompt→file edit bindings)."""
    p = root / "logs" / "edit_pairs.jsonl"
    if not p.exists():
        return []
    pairs = []
    for line in p.read_text(encoding="utf-8").strip().splitlines():
        try:
            pairs.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return pairs


def _load_rework_log(root: Path) -> list[dict[str, Any]]:
    """Load rework verdicts."""
    p = root / "rework_log.json"
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    return data.get("entries", data.get("events", []))


def _load_journal_window(root: Path, after_n: int, window: int) -> list[dict[str, Any]]:
    """Load journal entries in session_n range (after_n, after_n + window]."""
    p = root / "logs" / "prompt_journal.jsonl"
    if not p.exists():
        return []
    entries = []
    for line in p.read_text(encoding="utf-8").strip().splitlines():
        try:
            e = json.loads(line)
            sn = e.get("session_n", 0)
            if after_n < sn <= after_n + window:
                entries.append(e)
        except json.JSONDecodeError:
            continue
    return entries
