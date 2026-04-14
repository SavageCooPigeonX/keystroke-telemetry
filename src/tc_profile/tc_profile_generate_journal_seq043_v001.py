"""tc_profile_generate_journal_seq043_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 043 | VER: v001 | 26 lines | ~197 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from ..tc_constants import ROOT
import ast
import json
import re

def generate_profile_from_journal(n_prompts: int = 20) -> dict | None:
    """Generate a profile from the last N prompts in the journal.
    
    Convenience function for end-of-session profile generation.
    """
    journal = ROOT / 'logs' / 'prompt_journal.jsonl'
    if not journal.exists():
        return None
    
    prompts = []
    for line in journal.read_text('utf-8', errors='ignore').strip().splitlines()[-n_prompts:]:
        try:
            prompts.append(json.loads(line))
        except Exception:
            continue
    
    if not prompts:
        return None
    
    return generate_profile_from_session(prompts)
