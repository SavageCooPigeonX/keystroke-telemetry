"""codex_compat_render_staleness_alert_block_seq030_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 030 | VER: v002 | 24 lines | ~286 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
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
