"""predictor_seq009_cache_utils_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

def _cache_path(root: Path) -> Path:
    return root / "pigeon_brain" / PREDICTION_CACHE_FILE


def load_predictions(root: Path) -> list[dict[str, Any]]:
    """Load cached predictions."""
    p = _cache_path(root)
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        return data.get("predictions", [])
    return []


def save_predictions(root: Path, predictions: list[dict[str, Any]]) -> None:
    """Persist prediction cache."""
    p = _cache_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(
        {"predictions": predictions[-50:], "updated": datetime.now(timezone.utc).isoformat()},
        indent=2, default=str,
    ), encoding="utf-8")
