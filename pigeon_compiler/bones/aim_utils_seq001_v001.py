"""pigeon_compiler/bones/aim_utils_seq001_v001.py

BONE MODULE — Extracted from hush_aim_seq001_v001.py (v4.9.13)
Origin: Lines 1527-1600, last modified 2026-03-04/05

Text tokenizer + proper noun extractor used by AIM engines.
Pure regex operations — zero LLM calls. Zero session mutation.
"""
import re

_STOP_WORDS = frozenset({
    'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'shall', 'can', 'to', 'of', 'in', 'for',
    'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through', 'during',
    'before', 'after', 'above', 'below', 'between', 'out', 'off', 'up',
    'down', 'then', 'than', 'too', 'very', 'just', 'about', 'so', 'if',
    'or', 'and', 'but', 'not', 'no', 'nor', 'only', 'own', 'same',
    'that', 'this', 'these', 'those', 'it', 'its', 'i', 'me', 'my',
    'we', 'our', 'you', 'your', 'he', 'him', 'his', 'she', 'her',
    'they', 'them', 'their', 'what', 'which', 'who', 'whom', 'when',
    'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few',
    'more', 'most', 'other', 'some', 'such', 'any',
})


def tokenize(text: str) -> set[str]:
    """Extract meaningful tokens from text, excluding stop words."""
    words = re.findall(r'[a-zA-Z]{3,}', text.lower())
    return set(words) - _STOP_WORDS


_FALSE_PROPER_NOUNS = frozenset({
    'What', 'When', 'Where', 'Who', 'How', 'Why', 'Which', 'Can',
    'Could', 'Would', 'Should', 'Does', 'Have', 'Tell', 'Show',
    'Find', 'Search', 'Google', 'Look', 'Check', 'Run', 'Get',
    'List', 'Build', 'Load', 'Start', 'Stop', 'Hey', 'Yes', 'Yeah',
    'Please', 'Thanks', 'Also', 'Just', 'Like', 'Well', 'The',
    'This', 'That', 'These', 'Those', 'Some', 'Any', 'All', 'Most',
    'Let', 'Make', 'Give', 'Take', 'Put', 'Set', 'Try', 'Keep',
})


def extract_proper_nouns(message: str) -> list[str]:
    """Extract potential entity names (capitalized word sequences) from message.

    Finds multi-word names ("Benjamin Netanyahu") and single capitalized words
    (non-sentence-starters, 4+ chars). Filters common false positives.
    """
    names = []

    multi_word = re.findall(
        r'(?<![.\w])([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})',
        message,
    )
    for mw in multi_word:
        first_word = mw.split()[0]
        if first_word not in _FALSE_PROPER_NOUNS:
            names.append(mw)

    words = message.split()
    for i, w in enumerate(words):
        if i == 0:
            continue
        clean = re.sub(r'[^a-zA-Z]', '', w)
        if (
            clean
            and len(clean) >= 4
            and clean[0].isupper()
            and clean not in _FALSE_PROPER_NOUNS
            and not clean.isupper()
        ):
            already = any(clean in n for n in names)
            if not already:
                names.append(clean)

    return list(set(names))
