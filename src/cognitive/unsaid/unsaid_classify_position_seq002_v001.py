"""unsaid_classify_position_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
import re

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
