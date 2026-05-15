"""codex_compat_record_entropy_shed_seq070_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 070 | VER: v002 | 21 lines | ~257 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from .codex_compat_append_jsonl_seq005_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _append_jsonl
from .codex_compat_refresh_state_seq057_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import refresh_state
from .codex_compat_utc_now_seq001_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _utc_now
from pathlib import Path
from typing import Any
import json
import re

def record_entropy_shed(root: Path, module: str, confidence: float, note: str = "") -> dict[str, Any]:
    root = Path(root)
    entry = {
        "ts": _utc_now(),
        "module": module,
        "confidence": max(0.0, min(1.0, float(confidence))),
        "note": note,
        "source": "codex_explicit",
    }
    _append_jsonl(root / "logs" / "entropy_sheds.jsonl", entry)
    refresh_state(root, f"recorded entropy shed for {module}")
    return entry
