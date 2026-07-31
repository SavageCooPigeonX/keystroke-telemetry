"""codex_compat_seq034_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_seq001_v001 import _append_jsonl
from .codex_compat_seq001_v001 import _parse_deleted_words
from .codex_compat_seq001_v001 import _state_from_deletions
from .codex_compat_seq001_v001 import _utc_now
from .codex_compat_seq002_v001 import _ensure_repo_on_path
from .codex_compat_seq018_v001 import enqueue_deepseek_prompt_job
from .codex_compat_seq024_v001 import _fire_file_sim
from .codex_compat_seq025_v001 import _emit_codex_prompt_email
from .codex_compat_seq025_v001 import _record_intent_loop
from .codex_compat_seq030_v001 import select_context
from .codex_compat_seq031_v001 import refresh_state
from .codex_compat_seq033_v001 import _classify_intent
from .codex_compat_seq033_v001 import _load_json
from .codex_compat_seq033_v001 import _next_session_n
from .codex_compat_prompt_state_seq045_v001 import infer_prompt_cognitive_state
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import re

def log_prompt(
    root: Path,
    prompt: str,
    ts: str | None = None,
    session_n: int | None = None,
    deleted_words: list[str] | None = None,
    deleted_text: str = "",
    deletion_ratio: float | None = None,
    hesitation_count: int = 0,
    duration_ms: int = 0,
    total_keystrokes: int = 0,
    rewrites: list[dict[str, Any]] | None = None,
    source: str = "codex_explicit",
    fire_file_sim: bool = True,
    emit_prompt_email: bool = True,
) -> dict[str, Any]:
    root = Path(root)
    session_n = session_n or _next_session_n(root)
    prompt = prompt.strip()
    parsed_deleted_words = _parse_deleted_words(deleted_words, deleted_text)
    if deletion_ratio is None:
        deleted_chars = len(deleted_text)
        denominator = max(len(prompt) + deleted_chars, 1)
        deletion_ratio = round(deleted_chars / denominator, 3) if deleted_chars else 0
    deletion_ratio = max(0.0, min(1.0, float(deletion_ratio)))
    total_keystrokes = total_keystrokes or len(prompt) + len(deleted_text)
    entry = {
        "ts": ts or _utc_now(),
        "session_n": session_n,
        "session_id": f"codex-{datetime.now(timezone.utc).strftime('%Y%m%d')}",
        "msg": prompt,
        "intent": _classify_intent(prompt),
        "cognitive_state": infer_prompt_cognitive_state(
            prompt,
            _state_from_deletions(deletion_ratio, hesitation_count),
        ),
        "signals": {
            "wpm": 0,
            "chars_per_sec": 0,
            "deletion_ratio": deletion_ratio,
            "intent_deletion_ratio": deletion_ratio,
            "hesitation_count": hesitation_count,
            "rewrite_count": len(rewrites or []),
            "typo_corrections": 0,
            "intentional_deletions": len(parsed_deleted_words),
            "total_keystrokes": total_keystrokes,
            "duration_ms": duration_ms,
        },
        "deleted_words": parsed_deleted_words,
        "rewrites": rewrites or [],
        "module_refs": [],
        "source": source,
    }
    try:
        _ensure_repo_on_path(root)
        from src.tc_semantic_profile_seq001_v001 import log_semantic_profile_event
        entry["semantic_profile"] = log_semantic_profile_event(
            root,
            prompt,
            source=source,
            deleted_words=parsed_deleted_words,
        )
    except Exception as exc:
        entry["semantic_profile_error"] = str(exc)
    context = select_context(root, prompt, parsed_deleted_words, rewrites or [])
    entry["context_selection"] = context
    entry["file_sim"] = (
        _fire_file_sim(root, prompt, context_selection=context, trigger="log_prompt", force=True)
        if fire_file_sim
        else {"status": "skipped", "reason": "pre_prompt_will_fire", "trigger": "log_prompt"}
    )
    if prompt and fire_file_sim:
        entry["intent_loop"] = _record_intent_loop(
            root,
            prompt,
            context_selection=context,
            file_sim=entry.get("file_sim"),
            prompt_brain=_load_json(root / "logs" / "prompt_brain_latest.json") or {},
            source=source,
            deleted_words=parsed_deleted_words,
        )
    try:
        _ensure_repo_on_path(root)
        from src.opus_prompt_box_seq001_v001 import refine_opus_prompt_box

        entry["opus_prompt_box"] = refine_opus_prompt_box(root, prompt, write=True)
    except Exception as exc:
        entry["opus_prompt_box_error"] = str(exc)
    if prompt and emit_prompt_email:
        entry["codex_prompt_email"] = _emit_codex_prompt_email(root, entry, loop=entry.get("intent_loop"))
    _append_jsonl(root / "logs" / "prompt_journal.jsonl", entry)
    try:
        _ensure_repo_on_path(root)
        from src.ai_fingerprint_operator_seq001_v001 import build_operator_fingerprint
        build_operator_fingerprint(root)
    except Exception:
        pass
    try:
        enqueue_deepseek_prompt_job(
            root,
            prompt,
            context_selection=context,
            deleted_words=parsed_deleted_words,
            source=source,
            priority=4,
        )
    except Exception:
        pass
    refresh_state(root, "logged prompt")
    return entry
