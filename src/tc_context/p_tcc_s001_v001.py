"""tc_context_seq001_v001_cache_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 8 lines | ~58 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def invalidate_context_cache():
    """Force context reload on next call."""
    global _ctx_cache, _ctx_ts
    _ctx_cache = None
    _ctx_ts = 0
