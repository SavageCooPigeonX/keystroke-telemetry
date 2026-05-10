"""codex_compat_predict_numeric_files_seq017_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_load_intent_numeric_seq015_v001 import _load_intent_numeric
from pathlib import Path
from typing import Any
import re

def predict_numeric_files(root: Path, prompt: str, top_n: int = 6) -> list[dict[str, Any]]:
    root = Path(root)
    numeric = _load_intent_numeric(root)
    if numeric is None:
        return []
    try:
        predictions = []
        for item in numeric.predict_files(prompt, top_n=top_n) or []:
            if isinstance(item, dict):
                name = item.get("name") or item.get("file") or item.get("module")
                score = item.get("score", 0.0)
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                name, score = item[0], item[1]
            else:
                continue
            if name:
                predictions.append({"name": str(name), "score": score})
        return predictions
    except Exception:
        return []
