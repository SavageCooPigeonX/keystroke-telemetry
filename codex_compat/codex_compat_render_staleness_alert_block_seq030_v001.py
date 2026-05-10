"""codex_compat_render_staleness_alert_block_seq030_v001.py — Auto-extracted by Pigeon Compiler."""
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
