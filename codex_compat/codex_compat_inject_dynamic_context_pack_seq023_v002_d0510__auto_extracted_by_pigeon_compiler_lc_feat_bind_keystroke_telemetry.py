"""codex_compat_inject_dynamic_context_pack_seq023_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 023 | VER: v002 | 23 lines | ~298 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from .codex_compat_render_dynamic_context_pack_seq043_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _render_dynamic_context_pack
from .codex_compat_replace_managed_block_seq020_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _replace_managed_block
from .codex_compat_write_text_resilient_seq006_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _write_text_resilient
from pathlib import Path
from typing import Any
import re

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
