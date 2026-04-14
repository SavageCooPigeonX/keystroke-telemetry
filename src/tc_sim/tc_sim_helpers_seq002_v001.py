"""tc_sim_helpers_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 34 lines | ~293 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def _extract_continuation(buffer_at_pause: str, final_text: str) -> str:
    """What the operator typed AFTER the pause point."""
    if final_text.startswith(buffer_at_pause):
        return final_text[len(buffer_at_pause):]
    # Fuzzy: find best alignment
    for i in range(min(len(buffer_at_pause), len(final_text)), 0, -1):
        if final_text[:i] == buffer_at_pause[:i]:
            return final_text[i:]
    return final_text


def _word_overlap(prediction: str, actual: str) -> float:
    """Jaccard similarity of word sets."""
    pred_words = set(re.findall(r'\w+', prediction.lower()))
    actual_words = set(re.findall(r'\w+', actual.lower()))
    if not pred_words or not actual_words:
        return 0.0
    intersection = pred_words & actual_words
    union = pred_words | actual_words
    return len(intersection) / len(union)


def _prefix_match(prediction: str, actual: str) -> int:
    """How many characters match from the start."""
    n = 0
    for a, b in zip(prediction, actual):
        if a == b:
            n += 1
        else:
            break
    return n
