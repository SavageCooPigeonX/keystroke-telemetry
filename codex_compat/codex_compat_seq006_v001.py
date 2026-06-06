"""codex_compat_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_seq001_v001 import _append_jsonl
from .codex_compat_seq005_v001 import _load_intent_numeric
from pathlib import Path
from typing import Any
import json
import re

def train_numeric_surface(root: Path, prompt: str, files: list[str]) -> dict[str, Any]:
    root = Path(root)
    numeric = _load_intent_numeric(root)
    if numeric is None:
        return {"status": "missing", "files": files}
    try:
        numeric.record_touch(prompt, files)
        stats = numeric.get_stats()
        result = {
            "status": "ok",
            "files": files,
            "vocab_size": stats.get("vocab_size", 0),
            "files_tracked": stats.get("files_tracked", 0),
            "total_touches": stats.get("total_touches", 0),
        }
    except Exception as exc:
        result = {"status": "error", "error": str(exc), "files": files}
    _append_jsonl(root / "logs" / "numeric_training_history.jsonl", result)
    return result


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
