"""codex_compat_seq011_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_seq001_v001 import _parse_deleted_words
from .codex_compat_seq001_v001 import _utc_now
from .codex_compat_seq010_v001 import _running_prompt_summary
from .codex_compat_seq010_v001 import _task_queue_summary
from .codex_compat_seq016_v001 import _deepseek_default_model
from pathlib import Path
from typing import Any
import json
import os
import re

def _build_live_prompt_telemetry(root: Path, pack: dict[str, Any]) -> dict[str, Any]:
    signals = pack.get("signals") if isinstance(pack.get("signals"), dict) else {}
    context = pack.get("context_selection") if isinstance(pack.get("context_selection"), dict) else {}
    focus_files = pack.get("focus_files") if isinstance(pack.get("focus_files"), list) else []
    prompt_text = str(pack.get("prompt") or "")
    ts = str(pack.get("ts") or _utc_now())
    deleted_words = _parse_deleted_words(signals.get("deleted_words") if isinstance(signals.get("deleted_words"), list) else [], "")
    deepseek_job = pack.get("deepseek_job") if isinstance(pack.get("deepseek_job"), dict) else {}
    return {
        "schema": "prompt_telemetry/latest/v2",
        "updated_at": _utc_now(),
        "source": "codex_compat.dynamic_context_pack",
        "latest_prompt": {
            "session_n": None,
            "ts": ts,
            "chars": len(prompt_text),
            "preview": prompt_text[:240],
            "intent": context.get("intent_keys", prompt_text)[:240],
            "state": signals.get("cognitive_state") or "unknown",
            "files_open": [str(item.get("name")) for item in focus_files[:12] if isinstance(item, dict) and item.get("name")],
            "module_refs": [str(item.get("name")) for item in focus_files[:12] if isinstance(item, dict) and item.get("reason") == "numeric_context"],
        },
        "signals": {
            "wpm": 0,
            "chars_per_sec": 0,
            "deletion_ratio": signals.get("deletion_ratio", 0),
            "intent_deletion_ratio": signals.get("intent_deletion_ratio", 0),
            "hesitation_count": signals.get("hesitation_count", 0),
            "rewrite_count": 0,
            "typo_corrections": 0,
            "intentional_deletions": len(deleted_words),
            "total_keystrokes": max(len(prompt_text) + sum(len(w) for w in deleted_words), 0),
            "duration_ms": signals.get("duration_ms", 0),
        },
        "composition_binding": {
            "matched": True,
            "source": str(pack.get("surface") or "codex"),
            "age_ms": 0,
            "key": str(deepseek_job.get("job_id") or ""),
            "match_score": context.get("confidence", 0),
        },
        "deleted_words": deleted_words,
        "rewrites": [],
        "task_queue": _task_queue_summary(root),
        "hot_modules": [str(item.get("name")) for item in focus_files[:8] if isinstance(item, dict) and item.get("name")],
        "running_summary": _running_prompt_summary(root),
        "deepseek": {
            "model": deepseek_job.get("model") or _deepseek_default_model(),
            "job_id": deepseek_job.get("job_id") or "",
            "status": deepseek_job.get("status") or "not_queued",
            "autonomous_write": bool(deepseek_job.get("autonomous_write")),
        },
        "staleness": {
            "replaces_legacy_pigeon_prompt_telemetry": True,
            "fresh_source": "logs/dynamic_context_pack.json",
        },
    }
