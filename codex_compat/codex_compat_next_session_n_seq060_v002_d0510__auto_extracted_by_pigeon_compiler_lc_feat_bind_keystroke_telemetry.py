"""codex_compat_next_session_n_seq060_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 060 | VER: v002 | 14 lines | ~137 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from .codex_compat_load_jsonl_tail_seq007_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _load_jsonl_tail
from pathlib import Path
import json
import re

def _next_session_n(root: Path) -> int:
    rows = _load_jsonl_tail(root / "logs" / "prompt_journal.jsonl", max_lines=1)
    if not rows:
        return 1
    try:
        return int(rows[-1].get("session_n", 0)) + 1
    except (TypeError, ValueError):
        return 1
