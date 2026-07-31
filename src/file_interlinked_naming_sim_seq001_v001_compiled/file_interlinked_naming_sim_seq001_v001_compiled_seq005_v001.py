"""file_interlinked_naming_sim_seq001_v001_compiled_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_interlinked_naming_sim_seq001_v001_compiled_seq006_v001 import _git_last_subject
from pathlib import Path
from typing import Any
import json
import re

def _last_change_state(root: Path, file: str, kind: str) -> str:
    growth = _latest_growth_for_file(root, file)
    if growth:
        tags = ", ".join(growth.get("growth_tags") or [])
        key = growth.get("identity_key") or ""
        return f"{key}; tags={tags[:160]}"
    git_subject = _git_last_subject(root, file)
    if git_subject:
        return git_subject
    if kind == "symbolic_pigeon_name":
        return "keep glyph identity and append/update compact mutation-state tokens, not translation"
    if kind == "versioned_module":
        return "keep seq/version and compress the prose into the latest meaningful mutation phrase"
    if kind == "stable_facade":
        return "keep facade stable; store last change in manifest/memory rather than public import name"
    return "mirror the source behavior under test"


def _sibling_files(root: Path, file: str) -> list[str]:
    path = root / file
    parent = path.parent
    if not parent.exists():
        return []
    return [p.name for p in parent.glob("*.py")]


def _latest_growth_for_file(root: Path, file: str) -> dict[str, Any]:
    path = root / "logs" / "file_identity_growth.jsonl"
    if not path.exists():
        return {}
    rows = []
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[-400:]:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("file") == file:
                rows.append(row)
    except (OSError, json.JSONDecodeError):
        return {}
    return rows[-1] if rows else {}
