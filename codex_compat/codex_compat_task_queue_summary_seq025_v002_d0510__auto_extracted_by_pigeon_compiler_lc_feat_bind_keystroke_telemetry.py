"""codex_compat_task_queue_summary_seq025_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 025 | VER: v002 | 18 lines | ~231 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from .codex_compat_load_json_seq059_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _load_json
from pathlib import Path
from typing import Any
import json
import re

def _task_queue_summary(root: Path) -> dict[str, Any]:
    resolver = _load_json(root / "logs" / "codex_intent_resolver.json") or {}
    intents = resolver.get("intents") if isinstance(resolver.get("intents"), list) else []
    unresolved = [i for i in intents if i.get("status") not in {"done", "resolved"}]
    in_progress = [i for i in unresolved if i.get("status") == "partial"]
    return {
        "total": len(intents),
        "in_progress": [str(i.get("task") or i.get("source_key") or i.get("ts") or "") for i in in_progress[:8]],
        "pending": len(unresolved),
        "done": len(intents) - len(unresolved),
    }
