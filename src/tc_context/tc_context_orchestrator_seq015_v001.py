"""tc_context_orchestrator_seq015_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 015 | VER: v001 | 33 lines | ~256 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from ..tc_constants import ROOT
from pathlib import Path
import re
import time

from .tc_context_prompts_seq012_v001 import _load_context_recent_prompts
from .tc_context_telemetry_seq002_v001 import _load_context_telemetry
from .tc_context_unsaid_seq003_v001 import _load_context_unsaid_threads
from .tc_context_entropy_seq004_v001 import _load_context_entropy
from .tc_context_heatmap_seq005_v001 import _load_context_heat_map
from .tc_context_topology_seq006_v001 import _load_context_codebase_topology
from .tc_context_bugs_seq007_v001 import _load_context_bug_voices
from .tc_context_self_fix_seq008_v001 import _load_context_self_fix
from .tc_context_session_chat_seq013_v001 import _load_context_session_chat
from .tc_context_session_info_seq009_v001 import _load_context_session_info
from .tc_context_profiles_seq014_v001 import _load_context_file_profiles
from .tc_context_interrogation_seq010_v001 import _load_context_interrogation_answers
from .tc_context_organism_seq011_v001 import _load_context_organism_narrative

_ctx_cache = None
_ctx_ts = 0

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
