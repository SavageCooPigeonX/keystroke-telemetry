"""codex_compat_latest_json_seq019_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_load_jsonl_tail_seq007_v001 import _load_jsonl_tail
from pathlib import Path
from typing import Any
import json
import re

def _latest_json(path: Path) -> dict[str, Any] | None:
    rows = _load_jsonl_tail(path, max_lines=1)
    return rows[-1] if rows else None
