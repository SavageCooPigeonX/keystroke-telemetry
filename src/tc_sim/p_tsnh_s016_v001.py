"""tc_sim_seq001_v001_narrate_helpers_seq016_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 016 | VER: v001 | 25 lines | ~192 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from src.tc_constants_seq001_v001_seq001_v001 import KEYSTROKE_LOG, DEFAULT_PAUSE_MS, ROOT
import json
import re

def _narrate_context_signals() -> dict:
    """Load context signals for the narrative."""
    from src.tc_context_seq001_v001_seq001_v001 import load_context
    return load_context(ROOT)


def _narrate_sim_memory() -> dict:
    """Load sim memory for learning stats."""
    return _load_sim_memory()


def _narrate_profile() -> dict | None:
    """Load operator profile if it exists."""
    prof_path = ROOT / 'logs' / 'operator_profile_tc.json'
    if prof_path.exists():
        try:
            return json.loads(prof_path.read_text('utf-8', errors='ignore'))
        except Exception:
            pass
    return None
