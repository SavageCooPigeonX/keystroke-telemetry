"""pulse_harvest_seq015_utils_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
import hashlib
import re

def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:8]


def make_pulse_block(edit_ts: str = 'None',
                     edit_hash: str = 'None',
                     edit_why: str = 'None',
                     edit_state: str = 'idle') -> str:
    return (
        '# ── telemetry:pulse ──\n'
        f'# EDIT_TS:   {edit_ts}\n'
        f'# EDIT_HASH: {edit_hash}\n'
        f'# EDIT_WHY:  {edit_why}\n'
        f'# EDIT_STATE: {edit_state}\n'
        '# ── /pulse ──'
    )
