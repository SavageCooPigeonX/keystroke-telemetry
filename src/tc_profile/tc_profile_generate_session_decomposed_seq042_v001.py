"""tc_profile_generate_session_decomposed_seq042_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 042 | VER: v001 | 57 lines | ~474 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import Counter
import re

def generate_profile_from_session(prompts: list[dict], 
                                  profile_name: str | None = None) -> dict:
    """Generate an intent profile from a session's prompts.
    
    Call this at end of a session to learn a new profile.
    Returns the generated profile dict AND writes it to TC_MANIFEST.
    """
    if not prompts or len(prompts) < 3:
        return {}
    
    triggers = extract_session_triggers(prompts)
    files = extract_session_files(prompts)
    template = detect_session_template(prompts)
    
    if not triggers:
        return {}
    
    # Auto-generate name from top triggers if not provided
    if not profile_name:
        profile_name = '_'.join(triggers[:3])
    
    # Calculate confidence from session coherence
    # (more prompts with same intent = higher confidence)
    intents = [p.get('intent', 'unknown') for p in prompts]
    from collections import Counter
    intent_dist = Counter(intents)
    dominant_intent = intent_dist.most_common(1)[0] if intent_dist else ('unknown', 0)
    coherence = dominant_intent[1] / len(prompts) if prompts else 0
    confidence = min(0.95, 0.5 + coherence * 0.4)
    
    profile = {
        'trigger': triggers,
        'files': files,
        'template': template,
        'confidence': round(confidence, 2),
        'source_prompts': len(prompts),
    }
    
    # Write to TC_MANIFEST
    try:
        from ..tc_manifest import update_intent_profile
        update_intent_profile(
            name=profile_name,
            trigger=triggers,
            files=files,
            template=template,
            confidence=confidence,
            hit=True
        )
    except Exception:
        pass  # manifest might not exist yet
    
    return profile
