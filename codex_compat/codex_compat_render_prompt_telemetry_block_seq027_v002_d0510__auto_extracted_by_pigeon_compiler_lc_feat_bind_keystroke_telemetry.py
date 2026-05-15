"""codex_compat_render_prompt_telemetry_block_seq027_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 027 | VER: v002 | 20 lines | ~191 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from typing import Any
import json
import re

def _render_prompt_telemetry_block(telemetry: dict[str, Any]) -> str:
    return "\n".join([
        "<!-- pigeon:prompt-telemetry -->",
        "## Live Prompt Telemetry",
        "",
        f"*Auto-updated {telemetry.get('updated_at', '')} - source: `logs/prompt_telemetry_latest.json`*",
        "",
        "Use this block as the highest-freshness prompt-level telemetry. It is generated from Codex live context, not the stale legacy daemon.",
        "",
        "```json",
        json.dumps(telemetry, indent=2, ensure_ascii=False),
        "```",
        "",
        "<!-- /pigeon:prompt-telemetry -->",
    ])
