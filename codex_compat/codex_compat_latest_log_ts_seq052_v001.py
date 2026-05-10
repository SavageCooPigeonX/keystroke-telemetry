"""codex_compat_latest_log_ts_seq052_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_latest_json_seq019_v001 import _latest_json
from .codex_compat_load_json_seq059_v001 import _load_json
from .codex_compat_parse_iso_ts_seq051_v001 import _parse_iso_ts
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import re

def _latest_log_ts(root: Path, rel_path: str) -> tuple[datetime | None, dict[str, Any]]:
    path = root / rel_path
    if rel_path.endswith(".jsonl"):
        row = _latest_json(path) or {}
        return _parse_iso_ts(row.get("ts")), row
    data = _load_json(path) or {}
    return _parse_iso_ts(data.get("ts")), data
