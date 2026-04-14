"""u_pj_s019_v003_d0404_λNU_βoc_extract_composition_seq023_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 023 | VER: v001 | 46 lines | ~511 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def _log_enriched_entry_extract_from_composition(comp_match: dict, comp: dict) -> tuple:
    signals = {}
    deleted_words = []
    rewrites = []
    cog_state = 'unknown'
    binding = {
        'matched': False,
        'source': None,
        'age_ms': None,
        'key': None,
    }
    if comp_match and comp:
        binding = {
            'matched': True,
            'source': comp_match['source'],
            'age_ms': comp_match['age_ms'],
            'key': comp_match['key'],
            'match_score': round(comp_match['match_score'], 3),
        }
        cs = comp.get('chat_state', comp.get('signals', {}))
        sigs = cs.get('signals', cs) if isinstance(cs, dict) else {}
        signals = {
            'wpm':                sigs.get('wpm', 0),
            'chars_per_sec':      sigs.get('chars_per_sec', 0),
            'deletion_ratio':     sigs.get('deletion_ratio', comp.get('deletion_ratio', 0)),
            'hesitation_count':   sigs.get('hesitation_count', 0),
            'rewrite_count':      sigs.get('rewrite_count', 0),
            'typo_corrections':   comp.get('typo_corrections', sigs.get('typo_corrections', 0)),
            'intentional_deletions': comp.get('intentional_deletions', sigs.get('intentional_deletions', 0)),
            'total_keystrokes':   comp.get('total_keystrokes', 0),
            'duration_ms':        comp.get('duration_ms', 0),
        }
        cog_state = cs.get('state', 'unknown') if isinstance(cs, dict) else 'unknown'
        intent_deleted_words = [
            w.get('word', w) if isinstance(w, dict) else w
            for w in comp.get('intent_deleted_words', [])
        ]
        deleted_words = intent_deleted_words or [
            w.get('word', w) if isinstance(w, dict) else w
            for w in comp.get('deleted_words', [])
        ]
        rewrites = comp.get('rewrites', [])
    return signals, deleted_words, rewrites, cog_state, binding
