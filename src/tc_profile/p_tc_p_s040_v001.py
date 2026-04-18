"""tc_profile_seq001_v001_intent_template_seq040_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 040 | VER: v001 | 21 lines | ~243 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def detect_session_template(prompts: list[dict]) -> str:
    """Detect which template mode fits this session best.
    
    Returns: '/debug', '/build', or '/review'
    """
    intents = [p.get('intent', 'unknown') for p in prompts]
    states = [p.get('cognitive_state', 'unknown') for p in prompts]
    
    debug_signals = sum(1 for i in intents if i in ('debugging', 'fixing'))
    debug_signals += sum(1 for s in states if s in ('frustrated', 'hesitant'))
    
    build_signals = sum(1 for i in intents if i in ('building', 'creating', 'restructuring'))
    build_signals += sum(1 for s in states if s in ('focused', 'restructuring'))
    
    review_signals = sum(1 for i in intents if i in ('testing', 'reviewing', 'exploring'))
    
    scores = {'debug': debug_signals, 'build': build_signals, 'review': review_signals}
    return '/' + max(scores, key=scores.get)
