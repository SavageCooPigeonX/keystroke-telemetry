"""codex_compat_latest_json_seq019_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 019 | VER: v002 | 10 lines | ~109 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from .codex_compat_load_jsonl_tail_seq007_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _load_jsonl_tail
from pathlib import Path
from typing import Any
import json
import re

def _latest_json(path: Path) -> dict[str, Any] | None:
    rows = _load_jsonl_tail(path, max_lines=1)
    return rows[-1] if rows else None
