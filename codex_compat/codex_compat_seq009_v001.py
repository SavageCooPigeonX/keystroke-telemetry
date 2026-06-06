"""codex_compat_seq009_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_seq002_v001 import _write_text_resilient
from .codex_compat_seq007_v001 import _replace_managed_block
from .codex_compat_seq008_v001 import _render_pre_prompt_block
from .codex_compat_seq023_v001 import _render_dynamic_context_pack
from pathlib import Path
from typing import Any
import re

def _inject_pre_prompt_state(root: Path, state: dict[str, Any]) -> bool:
    path = root / ".github" / "copilot-instructions.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    block = _render_pre_prompt_block(state)
    updated = _replace_managed_block(
        text,
        "<!-- codex:pre-prompt-state -->",
        "<!-- /codex:pre-prompt-state -->",
        block,
    )
    if updated != text:
        _write_text_resilient(path, updated)
    return True


def _inject_dynamic_context_pack(root: Path, pack: dict[str, Any]) -> bool:
    path = root / ".github" / "copilot-instructions.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    block = _render_dynamic_context_pack(pack, managed=True)
    updated = _replace_managed_block(
        text,
        "<!-- codex:dynamic-context-pack -->",
        "<!-- /codex:dynamic-context-pack -->",
        block,
    )
    if updated != text:
        _write_text_resilient(path, updated)
    return True
