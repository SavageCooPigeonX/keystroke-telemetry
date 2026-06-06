"""file_self_sim_learning_seq001_seq040_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_self_sim_learning_seq001_seq038_v001 import _clean_rel
from pathlib import Path
from typing import Any
import json
import re

def _source_wake_bonus(rel: str) -> float:
    path = str(rel).replace("\\", "/")
    name = Path(path).name
    if name.startswith("test_") or "/test" in path:
        return -1.5
    if path.startswith("src/"):
        return 3.0
    if path.startswith("client/"):
        return 2.0
    return 0.0


def _add(
    bucket: dict[str, dict[str, Any]],
    rel: Any,
    points: float,
    reason: str,
    signal: str,
) -> None:
    clean = _clean_rel(rel)
    if not clean:
        return
    bucket[clean]["score"] += float(points)
    bucket[clean]["reasons"].append(reason)
    bucket[clean]["signals"][signal] += 1


def _dedupe(values: Any) -> list[Any]:
    seen = set()
    out = []
    for value in values or []:
        key = json.dumps(value, sort_keys=True, default=str) if isinstance(value, dict) else str(value)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
