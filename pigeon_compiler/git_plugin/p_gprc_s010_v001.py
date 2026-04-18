"""git_plugin_registry_churn_seq010_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 010 | VER: v001 | 13 lines | ~142 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import os
import re

def _registry_churn(registry: dict, top_n: int = 8) -> list[dict]:
    """Return top_n most-versioned modules — these are the pain points."""
    entries = list(registry.values())
    entries.sort(key=lambda e: e.get('ver', 1), reverse=True)
    return [
        {'module': e['name'], 'seq': e.get('seq'), 'ver': e.get('ver', 1),
         'tokens': e.get('tokens', 0), 'desc': e.get('desc', ''), 'intent': e.get('intent', '')}
        for e in entries[:top_n]
    ]
