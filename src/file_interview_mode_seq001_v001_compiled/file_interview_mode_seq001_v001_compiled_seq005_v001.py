"""file_interview_mode_seq001_v001_compiled_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_interview_mode_seq001_v001_compiled_seq007_v001 import _load_json
from .file_interview_mode_seq001_v001_compiled_seq008_v001 import _load_jsonl
from pathlib import Path
from typing import Any
import json
import re

def _context_questions_for_file(root: Path, rel: str) -> list[str]:
    stem = Path(rel).stem
    questions: list[str] = []
    for row in _load_jsonl(root / "logs" / "context_requests.jsonl", limit=200):
        module = str(row.get("module") or "")
        if module and (stem.startswith(module) or module.startswith(stem) or module in stem):
            questions.extend(str(q) for q in row.get("questions") or [])
    return list(dict.fromkeys(questions))


def _alias_for_file(root: Path, rel: str) -> dict[str, Any]:
    alias = _alias_for_key(root, rel)
    if alias:
        return alias
    stem = Path(rel).stem
    aliases = _load_json(root / "logs" / "file_identity_aliases.json") or {}
    rows = aliases.get("aliases") or {}
    for key, row in rows.items():
        current = str(row.get("current_file") or "").replace("\\", "/")
        if current == rel or Path(current).stem == stem:
            return {"alias": key, **row}
    return {"current_file": rel, "current_files": [rel], "status": "no_alias_record"}


def _alias_for_key(root: Path, key: str) -> dict[str, Any]:
    aliases = _load_json(root / "logs" / "file_identity_aliases.json") or {}
    rows = aliases.get("aliases") or {}
    return rows.get(key) or rows.get(str(key).lstrip("./")) or {}


def _same_identity(root: Path, left: str, right: str) -> bool:
    if not left or not right:
        return False
    left = left.replace("\\", "/")
    right = right.replace("\\", "/")
    if left == right:
        return True
    left_alias = _alias_for_file(root, left)
    right_alias = _alias_for_file(root, right)
    left_files = set(left_alias.get("current_files") or [left_alias.get("current_file", left)])
    right_files = set(right_alias.get("current_files") or [right_alias.get("current_file", right)])
    return bool(left_files & right_files) or Path(left).stem == Path(right).stem
