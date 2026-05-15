"""codex_compat_enqueue_deepseek_prompt_job_seq038_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 038 | VER: v002 | 68 lines | ~807 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from .codex_compat_append_jsonl_seq005_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _append_jsonl
from .codex_compat_deepseek_default_model_seq035_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _deepseek_default_model
from .codex_compat_load_jsonl_tail_seq007_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _load_jsonl_tail
from .codex_compat_parse_deleted_words_seq003_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _parse_deleted_words
from .codex_compat_utc_now_seq001_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _utc_now
from pathlib import Path
from typing import Any
import hashlib
import json
import os
import re

def enqueue_deepseek_prompt_job(
    root: Path,
    prompt: str,
    context_selection: dict[str, Any] | None = None,
    context_pack: dict[str, Any] | None = None,
    deleted_words: list[Any] | None = None,
    source: str = "codex_prompt",
    priority: int = 5,
    mode: str = "coding_context",
) -> dict[str, Any] | None:
    """Queue a DeepSeek V4 coding/context job for the next daemon cycle."""
    prompt = str(prompt or "").strip()
    if not prompt:
        return None
    root = Path(root)
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)

    context_selection = context_selection or (context_pack or {}).get("context_selection") or {}
    focus_files = (context_pack or {}).get("focus_files") or context_selection.get("files") or []
    signals = (context_pack or {}).get("signals") or {}
    parsed_deleted = _parse_deleted_words(deleted_words if deleted_words is not None else signals.get("deleted_words") or [], "")

    digest_src = json.dumps({
        "prompt": prompt,
        "source": source,
        "focus_files": focus_files[:8],
        "deleted_words": parsed_deleted[:12],
    }, sort_keys=True, ensure_ascii=False)
    job_id = "ds4-" + hashlib.sha256(digest_src.encode("utf-8")).hexdigest()[:16]

    recent = _load_jsonl_tail(logs / "deepseek_prompt_jobs.jsonl", max_lines=80)
    for row in recent:
        if row.get("job_id") == job_id:
            return {**row, "duplicate": True}

    job = {
        "ts": _utc_now(),
        "job_id": job_id,
        "status": "queued",
        "source": source,
        "mode": mode,
        "model": _deepseek_default_model(),
        "prompt": prompt,
        "deleted_words": parsed_deleted,
        "priority": priority,
        "focus_files": focus_files[:12],
        "context_confidence": context_selection.get("confidence", 0),
        "context_status": context_selection.get("status", "unknown"),
        "context_pack_path": "logs/dynamic_context_pack.json" if context_pack else "",
        "autonomous_write": os.environ.get("DEEPSEEK_AUTONOMOUS_PROMPT_WRITES", "").lower() in {"1", "true", "yes"},
    }
    _append_jsonl(logs / "deepseek_prompt_jobs.jsonl", job)
    (logs / "deepseek_prompt_latest.json").write_text(json.dumps(job, indent=2, ensure_ascii=False), encoding="utf-8")
    return job
