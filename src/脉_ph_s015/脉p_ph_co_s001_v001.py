"""pulse_harvest_seq015_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
import re

PULSE_RE = re.compile(
    r'^# ── telemetry:pulse ──\n'
    r'# EDIT_TS:\s*(.*)\n'
    r'# EDIT_HASH:\s*(.*)\n'
    r'# EDIT_WHY:\s*(.*)\n'
    r'(?:# EDIT_STATE:\s*(.*)\n)?'
    r'# ── /pulse ──$',
    re.MULTILINE,
)


PULSE_BLOCK = (
    '# ── telemetry:pulse ──\n'
    '# EDIT_TS:   None\n'
    '# EDIT_HASH: None\n'
    '# EDIT_WHY:  None\n'
    '# EDIT_STATE: idle\n'
    '# ── /pulse ──'
)
