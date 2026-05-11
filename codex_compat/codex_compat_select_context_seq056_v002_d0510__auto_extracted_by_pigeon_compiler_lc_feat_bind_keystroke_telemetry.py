"""codex_compat_select_context_seq056_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 056 | VER: v002 | 57 lines | ~588 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from .codex_compat_append_jsonl_seq005_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _append_jsonl
from .codex_compat_load_context_select_agent_seq014_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _load_context_select_agent
from .codex_compat_predict_numeric_files_seq017_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import predict_numeric_files
from .codex_compat_utc_now_seq001_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _utc_now
from pathlib import Path
from typing import Any
import json
import re

def select_context(
    root: Path,
    prompt: str,
    deleted_words: list[str] | None = None,
    rewrites: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    root = Path(root)
    agent = _load_context_select_agent()
    if agent is None:
        result = {
            "ts": _utc_now(),
            "buffer": prompt[:200],
            "intent_keys": prompt[:300],
            "files": [],
            "stale_blocks": [],
            "confidence": 0.0,
            "status": "missing_context_select_agent",
        }
    else:
        try:
            result = agent.run_assembly(root, prompt, deleted_words or [], rewrites or [])
            result["status"] = "ok"
        except Exception as exc:
            result = {
                "ts": _utc_now(),
                "buffer": prompt[:200],
                "intent_keys": prompt[:300],
                "files": [],
                "stale_blocks": [],
                "confidence": 0.0,
                "status": "error",
                "error": str(exc),
            }

    if not result.get("files"):
        numeric_files = predict_numeric_files(root, " ".join([prompt, *(deleted_words or [])]))
        if numeric_files:
            result["files"] = numeric_files
            result["confidence"] = numeric_files[0]["score"]
            result["fallback"] = "intent_numeric_direct"

    (root / "logs" / "context_selection.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    _append_jsonl(root / "logs" / "context_selection_history.jsonl", result)
    return result
