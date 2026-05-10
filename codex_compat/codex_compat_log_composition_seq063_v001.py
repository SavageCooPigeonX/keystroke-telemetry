"""codex_compat_log_composition_seq063_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_append_jsonl_seq005_v001 import _append_jsonl
from .codex_compat_build_unsaid_reconstruction_seq064_v001 import _build_unsaid_reconstruction
from .codex_compat_log_prompt_seq062_v001 import log_prompt
from .codex_compat_parse_deleted_words_seq003_v001 import _parse_deleted_words
from .codex_compat_refresh_state_seq057_v001 import refresh_state
from .codex_compat_utc_now_seq001_v001 import _utc_now
from .codex_compat_write_unsaid_seq065_v001 import _write_unsaid
from pathlib import Path
from typing import Any
import json
import os
import re

def log_composition(
    root: Path,
    final_text: str,
    deleted_text: str = "",
    deleted_words: list[str] | None = None,
    rewrites: list[dict[str, Any]] | None = None,
    hesitation_count: int = 0,
    duration_ms: int = 0,
    fire_file_sim: bool = True,
    emit_prompt_email: bool = True,
) -> dict[str, Any]:
    root = Path(root)
    parsed_deleted_words = _parse_deleted_words(deleted_words, deleted_text)
    deletion_ratio = round(len(deleted_text) / max(len(final_text) + len(deleted_text), 1), 3) if deleted_text else 0
    entry = {
        "ts": _utc_now(),
        "final_text": final_text,
        "deleted_text": deleted_text[:1000],
        "deleted_words": parsed_deleted_words,
        "intent_deleted_words": parsed_deleted_words,
        "deletion_ratio": deletion_ratio,
        "intent_deletion_ratio": deletion_ratio,
        "hesitation_windows": [{} for _ in range(max(0, hesitation_count))],
        "rewrites": rewrites or [],
        "total_keystrokes": len(final_text) + len(deleted_text),
        "duration_ms": duration_ms,
        "source": "codex_composition",
        "unsaid_reconstruction": _build_unsaid_reconstruction(final_text, parsed_deleted_words),
    }
    _append_jsonl(root / "logs" / "chat_compositions.jsonl", entry)
    _write_unsaid(root, entry)
    log_prompt(
        root,
        final_text,
        deleted_words=parsed_deleted_words,
        deleted_text=deleted_text,
        deletion_ratio=deletion_ratio,
        hesitation_count=hesitation_count,
        duration_ms=duration_ms,
        total_keystrokes=entry["total_keystrokes"],
        rewrites=rewrites,
        source="codex_composition",
        fire_file_sim=fire_file_sim,
        emit_prompt_email=emit_prompt_email,
    )
    refresh_state(root, "logged composition with deletions")
    return entry
