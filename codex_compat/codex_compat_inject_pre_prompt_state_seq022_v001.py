"""codex_compat_inject_pre_prompt_state_seq022_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_render_pre_prompt_block_seq021_v001 import _render_pre_prompt_block
from .codex_compat_replace_managed_block_seq020_v001 import _replace_managed_block
from .codex_compat_write_text_resilient_seq006_v001 import _write_text_resilient
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
