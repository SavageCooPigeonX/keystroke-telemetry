"""unsaid_classify_deletion_intent_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
import re

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
