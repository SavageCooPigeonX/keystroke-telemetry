"""codex_compat_emit_codex_prompt_email_seq046_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_ensure_repo_on_path_seq009_v001 import _ensure_repo_on_path
from pathlib import Path
from typing import Any
import re

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
