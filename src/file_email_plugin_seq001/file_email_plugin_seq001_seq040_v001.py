"""file_email_plugin_seq001_seq040_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq051_v001 import _load_json
from .file_email_plugin_seq001_seq051_v001 import _rel
from .file_email_plugin_seq001_seq052_v001 import DEFAULT_CONFIG
from .file_email_plugin_seq001_seq052_v001 import _write_json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import re

def _write_file_memory_index(root: Path, config: dict[str, Any]) -> None:
    memory_dir = root / str(config.get("memory_dir") or DEFAULT_CONFIG["memory_dir"])
    rows = []
    for path in sorted(memory_dir.glob("*.json"))[:5000]:
        data = _load_json(path)
        if not isinstance(data, dict):
            continue
        rows.append({
            "file": data.get("file"),
            "thread_id": data.get("thread_id"),
            "updated_at": data.get("updated_at"),
            "messages": len(data.get("messages") or []),
            "path": _rel(root, path),
            "markdown": _rel(root, path.with_suffix(".md")),
        })
    _write_json(root / "logs" / "file_memory_index.json", {
        "schema": "file_memory_index/v1",
        "ts": datetime.now(timezone.utc).isoformat(),
        "count": len(rows),
        "files": rows,
    })


def _bump(counter: dict[str, int], key: Any) -> None:
    text = str(key or "").strip()
    if text:
        counter[text] = int(counter.get(text, 0)) + 1


def _append_unique(values: list[str], value: str, limit: int = 80) -> None:
    text = str(value or "").strip()
    if text and text not in values:
        values.append(text)
    del values[:-limit]


def _top_counts(counts: Any, limit: int = 8) -> str:
    if not isinstance(counts, dict) or not counts:
        return "none"
    return ", ".join(f"{key}:{value}" for key, value in sorted(counts.items(), key=lambda item: (-int(item[1]), item[0]))[:limit])


def _dedupe_list(values: list[str]) -> list[str]:
    out = []
    seen = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out
