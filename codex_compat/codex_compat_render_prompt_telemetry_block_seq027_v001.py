"""codex_compat_render_prompt_telemetry_block_seq027_v001.py — Auto-extracted by Pigeon Compiler."""
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
