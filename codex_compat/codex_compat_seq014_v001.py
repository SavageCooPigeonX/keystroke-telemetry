"""codex_compat_seq014_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_seq002_v001 import _write_text_resilient
from .codex_compat_seq007_v001 import _replace_managed_block
from .codex_compat_seq013_v001 import _render_current_query_block
from pathlib import Path
from typing import Any
import re

def _render_staleness_alert_block(pack: dict[str, Any], telemetry: dict[str, Any]) -> str:
    context = pack.get("context_selection") if isinstance(pack.get("context_selection"), dict) else {}
    stale_blocks = [
        str(item) for item in (context.get("stale_blocks") or [])
        if str(item) not in {"current-query", "prompt-telemetry"}
    ]
    lines = [
        "<!-- pigeon:staleness-alert -->",
        "## Staleness Alert",
        "",
        f"*Checked {telemetry.get('updated_at', '')} - Codex live context refreshed*",
        "",
        "**Live replacements active:** `pigeon:current-query`, `pigeon:prompt-telemetry`, `codex:dynamic-context-pack`, DeepSeek V4 prompt queue.",
        "",
        f"**Legacy stale blocks still reported:** {', '.join(stale_blocks) if stale_blocks else 'none'}",
        "",
        "**Rule:** Prefer the Codex live blocks below over older commit-time or daemon-time sections.",
        "<!-- /pigeon:staleness-alert -->",
    ]
    return "\n".join(lines)


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
