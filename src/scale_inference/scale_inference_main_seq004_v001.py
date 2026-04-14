"""scale_inference_main_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 81 lines | ~728 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def infer_scale(fragment: str, cognitive_state: str = 'unknown',
                wpm: float = 0, del_ratio: float = 0) -> dict:
    """Infer the output scale from a typing fragment + operator state.

    Returns:
        {
            'scale': int (1-4),
            'label': str ('SENTENCE' | 'PARAGRAPH' | 'FULL_WRITE' | 'PAPER'),
            'reason': str (why this scale was chosen),
            'confidence': float (0-1),
        }
    """
    text = fragment.strip().lower()
    words = text.split()

    if not words:
        return {'scale': 1, 'label': 'SENTENCE', 'reason': 'empty', 'confidence': 0.1}

    # check "what if we ..." → PAPER
    if _WHAT_IF_PATTERN.search(text):
        return {'scale': 4, 'label': 'PAPER', 'reason': 'what_if_pattern', 'confidence': 0.8}

    # check "the [module]" alone → SENTENCE
    if _MODULE_PATTERN.match(text):
        return {'scale': 1, 'label': 'SENTENCE', 'reason': 'module_naming', 'confidence': 0.7}

    # scan for keyword matches — highest wins
    best_scale = 1
    best_reason = 'default'
    best_conf = 0.3

    for word in words:
        clean = re.sub(r'[^a-z]', '', word)
        if clean in _ARCHITECTURE_WORDS:
            s = _ARCHITECTURE_WORDS[clean]
            if s > best_scale:
                best_scale = s
                best_reason = f'architecture_word:{clean}'
                best_conf = 0.75
        elif clean in _ACTION_WORDS:
            s = _ACTION_WORDS[clean]
            if s > best_scale:
                best_scale = s
                best_reason = f'action_word:{clean}'
                best_conf = 0.7
        elif clean in _QUESTION_WORDS:
            s = _QUESTION_WORDS[clean]
            if s > best_scale:
                best_scale = s
                best_reason = f'question_word:{clean}'
                best_conf = 0.65

    # cognitive state modifier: FOCUSED + high WPM → upgrade one level
    # but cap at FULL_WRITE — PAPER requires explicit architecture words
    if cognitive_state in ('focused', 'flow') and wpm > 50:
        if best_scale < 3:
            best_scale += 1
            best_reason += '+flow_upgrade'
            best_conf = min(best_conf + 0.1, 0.95)

    # high deletion ratio → operator is restructuring → PARAGRAPH (explain first)
    if del_ratio > 0.4 and best_scale == 3:
        best_scale = 2
        best_reason += '+restructuring_downgrade'
        best_conf = max(best_conf - 0.1, 0.3)

    # fragment length heuristic: very long fragments suggest deep intent
    if len(words) > 12 and best_scale < 3:
        best_scale = min(best_scale + 1, 3)
        best_reason += '+long_fragment'

    label = SCALES.get(best_scale, 'SENTENCE')
    return {
        'scale': best_scale,
        'label': label,
        'reason': best_reason,
        'confidence': round(best_conf, 2),
    }
