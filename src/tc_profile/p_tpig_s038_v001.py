"""tc_profile_seq001_v001_intent_generation_seq038_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 038 | VER: v001 | 65 lines | ~679 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import re

def extract_session_triggers(prompts: list[dict], min_count: int = 2) -> list[str]:
    """Extract recurring intent words from a session's prompts.
    
    Returns words that appear in 2+ prompts (configurable), sorted by frequency.
    These become trigger words for the new intent profile.
    """
    word_count: dict[str, int] = {}
    for p in prompts:
        msg = p.get('msg', '').lower()
        # Extract meaningful words
        words = set(re.findall(r'[a-zA-Z_][a-zA-Z0-9_]+', msg))
        for w in words:
            if len(w) > 3 and w not in _INTENT_STOPWORDS:
                word_count[w] = word_count.get(w, 0) + 1
    
    # Filter to words appearing in min_count+ prompts
    triggers = [(w, c) for w, c in word_count.items() if c >= min_count]
    triggers.sort(key=lambda x: -x[1])
    return [w for w, c in triggers[:15]]  # top 15


def extract_session_files(prompts: list[dict]) -> list[str]:
    """Extract files mentioned/touched in a session.
    
    Sources: files_open field, module_refs field, and text mentions.
    """
    files = set()
    for p in prompts:
        for f in p.get('files_open', []):
            if f:
                files.add(Path(f).stem if '/' in f or '\\' in f else f)
        for ref in p.get('module_refs', []):
            if ref:
                files.add(ref.split('_seq')[0] if '_seq' in ref else ref)
        # Also extract tc_* and *_manifest mentions from text
        msg = p.get('msg', '')
        tc_mentions = re.findall(r'tc_\w+', msg.lower())
        files.update(tc_mentions)
        manifest_mentions = re.findall(r'\w*manifest\w*', msg.lower())
        files.update(m for m in manifest_mentions if len(m) > 5)
    return list(files)[:10]


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
