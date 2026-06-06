"""batch_rewrite_sim_seq001_seq028_v001.py — Auto-extracted by Pigeon Compiler."""
from .batch_rewrite_sim_seq001_seq032_v001 import _referenced_by
from .batch_rewrite_sim_seq001_seq034_v001 import SOURCE_SUFFIXES
from .batch_rewrite_sim_seq001_seq034_v001 import _load_json
from pathlib import Path
from typing import Any
import json
import os
import re

def _resolve_alias_targets(root: Path, key: str) -> list[str]:
    normalized = str(key or "").strip().replace("\\", "/")
    if not normalized:
        return []
    aliases = _load_json(root / "logs" / "file_identity_aliases.json")
    if not isinstance(aliases, dict):
        return []
    rows = aliases.get("aliases") or {}
    if not isinstance(rows, dict):
        return []
    record = rows.get(normalized) or rows.get(normalized.lstrip("./"))
    if not isinstance(record, dict):
        return []
    current = [
        str(item).replace("\\", "/")
        for item in (record.get("current_files") or [])
        if str(item).strip()
    ]
    if not current and record.get("current_file"):
        current = [str(record.get("current_file")).replace("\\", "/")]
    return [item for item in dict.fromkeys(current) if (root / item).exists()]


def _metadata_candidate(path: str, tokens: set[str]) -> bool:
    lower = path.lower().replace("\\", "/")
    if tokens & {"manifest", "manifests", "docs", "document", "documentation"}:
        return False
    return lower.endswith("/manifest.md") or lower.endswith("manifest.md")


def _source_candidate(path: str) -> bool:
    return Path(path).suffix.lower() in SOURCE_SUFFIXES


def _cross_file_validation(root: Path, rel: str, dirty: set[str]) -> dict[str, Any]:
    path = root / rel
    out = {"exists": path.exists(), "dirty": rel in dirty, "line_count": 0, "imports": [], "referenced_by": []}
    if not path.exists() or not path.is_file():
        return out
    text = path.read_text(encoding="utf-8", errors="ignore")
    out["line_count"] = len(text.splitlines())
    out["imports"] = [ln.strip() for ln in text.splitlines() if ln.lstrip().startswith(("import ", "from "))][:12]
    out["referenced_by"] = _referenced_by(root, path.stem, rel)[:8]
    return out
