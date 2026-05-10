"""codex_compat_write_copilot_live_query_blocks_seq031_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_render_current_query_block_seq029_v001 import _render_current_query_block
from .codex_compat_render_staleness_alert_block_seq030_v001 import _render_staleness_alert_block
from .codex_compat_replace_managed_block_seq020_v001 import _replace_managed_block
from .codex_compat_write_text_resilient_seq006_v001 import _write_text_resilient
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
