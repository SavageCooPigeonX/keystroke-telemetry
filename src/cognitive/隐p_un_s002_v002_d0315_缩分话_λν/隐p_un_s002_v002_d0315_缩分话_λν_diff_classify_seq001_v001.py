"""隐p_un_s002_v002_d0315_缩分话_λν_diff_classify_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 45 lines | ~397 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
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
