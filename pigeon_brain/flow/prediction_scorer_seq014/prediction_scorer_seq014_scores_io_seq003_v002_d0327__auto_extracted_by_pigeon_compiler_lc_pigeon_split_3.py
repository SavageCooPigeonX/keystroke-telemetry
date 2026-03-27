"""prediction_scorer_seq014_scores_io_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v002 | 20 lines | ~181 tokens
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
