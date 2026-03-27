"""prediction_scorer_seq014_data_loaders_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v002 | 62 lines | ~514 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: pigeon_split_3
# LAST:   2026-03-27 @ fd07906
# SESSIONS: 1
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import re

def _load_scores(root: Path) -> list[dict[str, Any]]:
    p = _scores_path(root)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8")).get("scores", [])
    return []


def _save_scores(root: Path, scores: list[dict[str, Any]]) -> None:
    p = _scores_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = {"scores": scores[-MAX_SCORED:],
            "updated_at": datetime.now(timezone.utc).isoformat()}
    p.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


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
