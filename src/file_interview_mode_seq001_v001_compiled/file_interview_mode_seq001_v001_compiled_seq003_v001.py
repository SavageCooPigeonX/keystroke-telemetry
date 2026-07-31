"""file_interview_mode_seq001_v001_compiled_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_interview_mode_seq001_v001_compiled_seq004_v001 import _find_by_stem
from .file_interview_mode_seq001_v001_compiled_seq005_v001 import _alias_for_key
from .file_interview_mode_seq001_v001_compiled_seq006_v001 import _latest_push_cycle
from .file_interview_mode_seq001_v001_compiled_seq007_v001 import _load_json
from .file_interview_mode_seq001_v001_compiled_seq008_v001 import _load_jsonl
from pathlib import Path
import json
import re

def _recent_learning_files(root: Path) -> list[str]:
    files: list[str] = []
    latest_policy = _load_json(root / "logs" / "operator_response_policy_latest.json") or {}
    for comment in latest_policy.get("file_comments") or []:
        value = comment.get("file") or comment.get("path")
        if value:
            files.append(str(value))

    push = _latest_push_cycle(root)
    for module in push.get("modules_touched") or []:
        match = _find_by_stem(root, str(module))
        if match:
            files.append(match)

    for row in _load_jsonl(root / "logs" / "context_requests.jsonl", limit=60):
        module = row.get("module")
        if module:
            match = _find_by_stem(root, str(module))
            if match:
                files.append(match)
    return list(dict.fromkeys(files))


def _resolve_file(root: Path, value: str) -> Path | None:
    normalized = str(value or "").strip().replace("\\", "/")
    if not normalized:
        return None
    direct = root / normalized
    if direct.exists() and direct.is_file():
        return direct
    alias = _alias_for_key(root, normalized)
    current = alias.get("current_file") if alias else ""
    if current:
        resolved = root / current
        if resolved.exists() and resolved.is_file():
            return resolved
    stem = Path(normalized).stem
    match = _find_by_stem(root, stem)
    return root / match if match else None
