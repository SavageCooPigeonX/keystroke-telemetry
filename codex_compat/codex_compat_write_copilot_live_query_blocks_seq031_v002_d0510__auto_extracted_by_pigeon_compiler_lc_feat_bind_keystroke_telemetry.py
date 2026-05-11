"""codex_compat_write_copilot_live_query_blocks_seq031_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 031 | VER: v002 | 28 lines | ~383 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from .codex_compat_render_current_query_block_seq029_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _render_current_query_block
from .codex_compat_render_staleness_alert_block_seq030_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _render_staleness_alert_block
from .codex_compat_replace_managed_block_seq020_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _replace_managed_block
from .codex_compat_write_text_resilient_seq006_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _write_text_resilient
from pathlib import Path
from typing import Any
import re

def _write_copilot_live_query_blocks(root: Path, pack: dict[str, Any], telemetry: dict[str, Any]) -> None:
    path = root / ".github" / "copilot-instructions.md"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8", errors="ignore")
    updated = _replace_managed_block(
        text,
        "<!-- pigeon:current-query -->",
        "<!-- /pigeon:current-query -->",
        _render_current_query_block(pack),
    )
    updated = _replace_managed_block(
        updated,
        "<!-- pigeon:staleness-alert -->",
        "<!-- /pigeon:staleness-alert -->",
        _render_staleness_alert_block(pack, telemetry),
    )
    if updated != text:
        _write_text_resilient(path, updated)
