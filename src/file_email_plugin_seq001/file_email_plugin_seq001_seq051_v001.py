"""file_email_plugin_seq001_seq051_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_email_plugin_seq001_seq023_v001 import _failed_checks
from pathlib import Path
from typing import Any
import json
import os
import re

def _closing_argument(file_path: str, beef: str, record: dict[str, Any]) -> str:
    if record.get("event_type") == "compile":
        return f"`{Path(file_path).name}` will accept a rewrite when `{Path(beef).name}` is in the room and validation signs the minutes."
    if record.get("event_type") == "submission":
        return "`prompt_submission` opened the case file. The files may now testify, but nobody gets overwritten without approval."
    if record.get("event_type") == "completion":
        failed = _failed_checks(record)
        if failed:
            keys = ", ".join(str(item.get("key", "unknown")) for item in failed[:3])
            return f"`intent_completion` filed the receipt, then refused to smile because `{keys}` still failed."
        return "`intent_completion` closed the loop, stamped the receipt, and left a training crumb for future routing."
    if record.get("event_type") == "codex_prompt":
        return "`codex_prompt` heard the operator directly and filed a dev-surface receipt before any web-chat lane could touch it."
    if record.get("event_type") == "file_opinion":
        return "`pipeline_audit` made the file speak from current logs instead of pretending stale data was fine."
    return f"`{Path(file_path).name}` changed in the operator-state lane and will keep future mail centered on the actual work."


def _enabled(config: dict[str, Any], trigger: str) -> bool:
    return bool(config.get("enabled", True)) and trigger in set(config.get("triggers") or [])


def _safe_mailbox(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_.-]+", ".", value.lower()).strip(".")
    return clean[:48] or "file"


def _safe_filename(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("_")
    return clean[:120] or "file_email"


def _safe_tag(value: Any) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(value).lower()).strip("_")
    return clean[:60] or "file"


def _rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None
