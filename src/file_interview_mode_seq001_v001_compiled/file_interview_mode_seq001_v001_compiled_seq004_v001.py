"""file_interview_mode_seq001_v001_compiled_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_interview_mode_seq001_v001_compiled_seq005_v001 import _same_identity
from .file_interview_mode_seq001_v001_compiled_seq007_v001 import _load_json
from .file_interview_mode_seq001_v001_compiled_seq008_v001 import _rel
from pathlib import Path
from typing import Any
import json
import re

def _find_by_stem(root: Path, stem: str) -> str:
    clean = Path(stem).stem
    if not clean:
        return ""
    candidates = []
    for folder in ("src", "codex_compat", "pigeon_compiler", "tests", "scripts"):
        base = root / folder
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if path.stem == clean or path.stem.startswith(clean):
                candidates.append(path)
    if not candidates:
        return ""
    candidates.sort(key=lambda item: (len(item.name), item.as_posix()))
    return _rel(root, candidates[0])


def _file_profile(text: str) -> dict[str, str]:
    stripped = text.lstrip()
    says = ""
    if stripped.startswith(('"""', "'''")):
        quote = stripped[:3]
        end = stripped.find(quote, 3)
        says = stripped[3:end].strip().splitlines()[0] if end > 3 else ""
    if not says:
        for line in text.splitlines():
            clean = line.strip()
            if clean:
                says = clean[:180]
                break
    return {"says": says or "I do not have a readable opening statement."}


def _comments_for_file(root: Path, rel: str) -> list[dict[str, Any]]:
    policy = _load_json(root / "logs" / "operator_response_policy_latest.json") or {}
    out = []
    for comment in policy.get("file_comments") or []:
        path = str(comment.get("file") or comment.get("path") or "").replace("\\", "/")
        if _same_identity(root, rel, path):
            out.append({
                "file_says": comment.get("file_says", ""),
                "file_fix_proposal": comment.get("file_fix_proposal", ""),
                "fix_grade": comment.get("fix_grade", {}),
            })
    return out
