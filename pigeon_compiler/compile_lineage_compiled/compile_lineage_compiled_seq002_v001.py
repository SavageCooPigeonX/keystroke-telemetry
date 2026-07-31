"""compile_lineage_compiled_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from .compile_lineage_compiled_seq005_v001 import _load_json
from pathlib import Path
from typing import Any
import json
import re

def resolve_identity_alias(root: Path, key: str) -> dict[str, Any]:
    """Resolve a remembered path or source symbol through compile aliases."""
    aliases = _load_json(Path(root) / "logs" / "file_identity_aliases.json")
    if not isinstance(aliases, dict):
        return {}
    normalized = str(key or "").strip().replace("\\", "/")
    rows = aliases.get("aliases") or {}
    if not isinstance(rows, dict):
        return {}
    return rows.get(normalized) or rows.get(normalized.lstrip("./")) or {}
