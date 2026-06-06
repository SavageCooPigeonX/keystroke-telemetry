"""codex_compat_seq025_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_seq002_v001 import _ensure_repo_on_path
from pathlib import Path
from typing import Any
import os
import re

def _record_intent_loop(
    root: Path,
    prompt: str,
    context_selection: dict[str, Any] | None = None,
    file_sim: dict[str, Any] | None = None,
    prompt_brain: dict[str, Any] | None = None,
    source: str = "prompt",
    deleted_words: list[str] | None = None,
) -> dict[str, Any]:
    try:
        _ensure_repo_on_path(root)
        from src.intent_loop_closer_seq001_v001 import record_intent_loop
        return record_intent_loop(
            root,
            prompt,
            context_selection=context_selection,
            file_sim=file_sim,
            prompt_brain=prompt_brain,
            source=source,
            deleted_words=deleted_words,
        )
    except Exception as exc:
        return {"status": "error", "error": str(exc), "source": source}


def _emit_codex_prompt_email(
    root: Path,
    prompt_entry: dict[str, Any],
    loop: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        _ensure_repo_on_path(root)
        from src.file_email_plugin_seq001_v001 import emit_codex_prompt_email
        return emit_codex_prompt_email(root, prompt_entry, loop=loop)
    except Exception as exc:
        return {"status": "error", "phase": "codex_prompt", "error": str(exc)}


def _bind_intent_loop_response(root: Path, response_entry: dict[str, Any]) -> dict[str, Any]:
    try:
        _ensure_repo_on_path(root)
        from src.intent_loop_closer_seq001_v001 import bind_response_to_latest_loop
        return bind_response_to_latest_loop(root, response_entry)
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
