"""unsaid_seq002_helpers_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

import re

def _diff_deleted(before: str, after: str) -> str:
    """Find text that was in 'before' but removed in 'after'."""
    if after in before:
        idx = before.find(after)
        deleted_before = before[:idx]
        deleted_after = before[idx + len(after):]
        return (deleted_before + deleted_after).strip()
    if len(before) <= len(after):
        return ''
    common_start = 0
    for i in range(min(len(before), len(after))):
        if before[i] == after[i]:
            common_start = i + 1
        else:
            break
    return before[common_start:len(before) - max(0, len(after) - common_start)].strip()


def _classify_position(full_text: str, deleted: str) -> str:
    """Classify where in the message the deletion occurred."""
    pos = full_text.find(deleted)
    if pos < 0:
        return 'unknown'
    ratio = pos / max(len(full_text), 1)
    if ratio < 0.25:
        return 'beginning'
    elif ratio < 0.75:
        return 'middle'
    return 'end'


def _classify_deletion_intent(text: str) -> str:
    """Classify the cognitive intent behind a deletion."""
    if len(text) > 50:
        return 'full_restart'
    if re.search(r'\?$', text.strip()):
        return 'question_abandoned'
    if re.search(r'^(can you|could you|would you|please|help)', text.strip(), re.I):
        return 'request_abandoned'
    if re.search(r'^(i think|i feel|maybe|actually)', text.strip(), re.I):
        return 'thought_suppressed'
    return 'general_edit'


def _extract_topic(text: str) -> str:
    """Extract a rough topic label from text (first few meaningful words)."""
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    stopwords = {'the', 'and', 'for', 'that', 'this', 'with', 'from', 'are', 'was', 'you', 'can', 'how'}
    meaningful = [w for w in words if w not in stopwords][:4]
    return ' '.join(meaningful) if meaningful else text[:30].strip()
