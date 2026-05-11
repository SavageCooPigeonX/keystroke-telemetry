"""codex_compat_train_numeric_surface_seq016_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 016 | VER: v002 | 27 lines | ~306 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from .codex_compat_append_jsonl_seq005_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _append_jsonl
from .codex_compat_load_intent_numeric_seq015_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _load_intent_numeric
from pathlib import Path
from typing import Any
import json
import re

def train_numeric_surface(root: Path, prompt: str, files: list[str]) -> dict[str, Any]:
    root = Path(root)
    numeric = _load_intent_numeric(root)
    if numeric is None:
        return {"status": "missing", "files": files}
    try:
        numeric.record_touch(prompt, files)
        stats = numeric.get_stats()
        result = {
            "status": "ok",
            "files": files,
            "vocab_size": stats.get("vocab_size", 0),
            "files_tracked": stats.get("files_tracked", 0),
            "total_touches": stats.get("total_touches", 0),
        }
    except Exception as exc:
        result = {"status": "error", "error": str(exc), "files": files}
    _append_jsonl(root / "logs" / "numeric_training_history.jsonl", result)
    return result
