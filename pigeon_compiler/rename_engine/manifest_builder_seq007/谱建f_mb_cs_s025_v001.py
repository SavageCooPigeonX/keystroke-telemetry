"""manifest_builder_seq007_classify_state_seq025_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def _classify_msg_state(msg: dict) -> str:
    """Lightweight cognitive state classification for summary display."""
    keys = max(msg.get('total_keystrokes', 0), 1)
    dels = msg.get('total_deletions', 0)
    hes = msg.get('hesitation_score', 0.0)
    del_ratio = dels / keys
    if msg.get('deleted'):
        return 'abandoned'
    if hes > 0.6:
        return 'frustrated'
    if hes > 0.4:
        return 'hesitant'
    if del_ratio > 0.20:
        return 'restructuring'
    if hes < 0.15 and del_ratio < 0.05:
        return 'flow'
    if hes < 0.25:
        return 'focused'
    return 'neutral'
