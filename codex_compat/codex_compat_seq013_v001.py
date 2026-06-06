"""codex_compat_seq013_v001.py — Auto-extracted by Pigeon Compiler."""
from .codex_compat_seq001_v001 import _parse_deleted_words
from typing import Any
import re

def _render_current_query_block(pack: dict[str, Any]) -> str:
    context = pack.get("context_selection") if isinstance(pack.get("context_selection"), dict) else {}
    signals = pack.get("signals") if isinstance(pack.get("signals"), dict) else {}
    files = context.get("files") if isinstance(context.get("files"), list) else []
    file_names = [str(item.get("name")) for item in files if isinstance(item, dict) and item.get("name")]
    stale_blocks = [
        str(item) for item in (context.get("stale_blocks") or [])
        if str(item) not in {"current-query", "prompt-telemetry"}
    ]
    deleted = _parse_deleted_words(signals.get("deleted_words") if isinstance(signals.get("deleted_words"), list) else [], "")
    deepseek = pack.get("deepseek_job") if isinstance(pack.get("deepseek_job"), dict) else {}
    lines = [
        "<!-- pigeon:current-query -->",
        "## What You Actually Mean Right Now",
        "",
        f"*Assembled {pack.get('ts', '')} - codex_compat dynamic context - zero LLM calls*",
        "",
        f"**INTENT KEYS:** `{context.get('intent_keys') or pack.get('prompt') or ''}`",
        "",
        f"**FILES:** {', '.join(file_names[:8]) if file_names else 'none'}",
        "",
        f"**LEGACY_STALE_BLOCKS:** {', '.join(stale_blocks) if stale_blocks else 'none'}",
        "",
        f"**LIVE_REPLACEMENTS:** dynamic-context-pack, prompt-telemetry/latest/v2, DeepSeek V4 job `{deepseek.get('job_id', '')}`",
        "",
        f"**DELETED WORDS:** {', '.join(deleted) if deleted else 'none'}",
        "",
        f"**COGNITIVE STATE:** `{signals.get('cognitive_state') or 'unknown'}`",
        "<!-- /pigeon:current-query -->",
    ]
    return "\n".join(lines)
