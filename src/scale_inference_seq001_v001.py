"""scale_inference_seq001_v001.py — infer output scale from fragment intent density.

Maps typing fragments to output SCALE:
  SCALE 1 — SENTENCE: quick lookup, naming, short answers
  SCALE 2 — PARAGRAPH: explanation + code sketch + affected files
  SCALE 3 — FULL_WRITE: complete patch + test + manifest
  SCALE 4 — PAPER: full technical document + architecture

Scale is inferred from:
  - Action verbs ("fix", "add", "wire" → FULL_WRITE)
  - Question words ("why", "how", "what if" → PARAGRAPH)
  - Architecture words ("redesign", "merge", "rethink" → PAPER)
  - Module naming alone → SENTENCE
  - Cognitive state: FOCUSED + high WPM → auto-upgrade one level

Usage:
    from src.scale_inference_seq001_v001_seq001_v001 import infer_scale, SCALES
    scale = infer_scale("fix the hardcoded import in", cognitive_state="focused", wpm=62)
"""
from __future__ import annotations
import re

SCALES = {
    1: 'SENTENCE',
    2: 'PARAGRAPH',
    3: 'FULL_WRITE',
    4: 'PAPER',
}

# keyword → base scale
_ACTION_WORDS = {
    'fix': 3, 'add': 3, 'wire': 3, 'patch': 3, 'implement': 3, 'build': 3,
    'create': 3, 'write': 3, 'remove': 3, 'delete': 3, 'replace': 3,
    'refactor': 3, 'move': 3, 'rename': 3, 'split': 3, 'merge': 3,
    'connect': 3, 'hook': 3, 'plug': 3, 'inject': 3, 'update': 3,
}

_QUESTION_WORDS = {
    'why': 2, 'how': 2, 'what': 2, 'explain': 2, 'show': 2,
    'describe': 2, 'compare': 2, 'analyze': 2, 'audit': 2,
    'check': 2, 'review': 2, 'investigate': 2, 'debug': 2,
}

_ARCHITECTURE_WORDS = {
    'redesign': 4, 'rethink': 4, 'rearchitect': 4, 'plan': 4,
    'strategy': 4, 'roadmap': 4, 'document': 4, 'paper': 4,
    'proposal': 4, 'migration': 4, 'overhaul': 4,
}

# "the [module_name]" alone = just lookup
_MODULE_PATTERN = re.compile(r'^the\s+[a-zA-Z_][a-zA-Z0-9_]*\s*$', re.IGNORECASE)

# "what if we [big word]" = paper
_WHAT_IF_PATTERN = re.compile(r'what\s+if\s+we\s+\w+', re.IGNORECASE)


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


def scale_to_token_budget(scale: int) -> int:
    """Map scale to approximate max output tokens for LLM B."""
    return {1: 150, 2: 600, 3: 2000, 4: 4000}.get(scale, 600)


def scale_to_instructions(scale: int) -> str:
    """Generate scale-specific instructions for LLM B."""
    if scale == 1:
        return (
            "Output: ONE sentence. The insight, the answer, the fact. "
            "No code unless the answer IS code. No explanation."
        )
    elif scale == 2:
        return (
            "Output: ONE paragraph. Explanation + code sketch if relevant + "
            "affected files. Enough to understand before committing."
        )
    elif scale == 3:
        return (
            "Output: FULL implementation. Complete code patch + test cases + "
            "manifest updates + push narrative. Don't explain — DO."
        )
    elif scale == 4:
        return (
            "Output: FULL technical document. Architecture rationale. "
            "Alternatives considered. Migration plan. Risk analysis. "
            "Code examples. Integration steps."
        )
    return "Output: brief, contextual response."
