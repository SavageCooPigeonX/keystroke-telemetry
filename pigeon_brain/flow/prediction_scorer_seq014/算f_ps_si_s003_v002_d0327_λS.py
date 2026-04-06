"""prediction_scorer_seq014_scores_io_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

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
