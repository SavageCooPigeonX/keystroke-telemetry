"""tc_context_orchestrator_seq015_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 015 | VER: v001 | 33 lines | ~256 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from .tc_constants import ROOT
from pathlib import Path
import re
import time

def load_context(repo_root: Path | None = None) -> dict:
    """Load all context sources with 120s caching."""
    global _ctx_cache, _ctx_ts
    now = time.time()
    if _ctx_cache is not None and (now - _ctx_ts) < 120:
        return _ctx_cache

    r = repo_root or ROOT
    ctx: dict = {}

    _load_context_recent_prompts(ctx, r)
    _load_context_telemetry(ctx, r)
    _load_context_unsaid_threads(ctx, r)
    _load_context_entropy(ctx, r)
    _load_context_heat_map(ctx, r)
    _load_context_codebase_topology(ctx, r)
    _load_context_bug_voices(ctx, r)
    _load_context_self_fix(ctx, r)
    _load_context_session_chat(ctx, r)
    _load_context_session_info(ctx, r)
    _load_context_file_profiles(ctx, r)
    _load_context_interrogation_answers(ctx, r)
    _load_context_organism_narrative(ctx, r)

    _ctx_cache = ctx
    _ctx_ts = now
    return ctx
