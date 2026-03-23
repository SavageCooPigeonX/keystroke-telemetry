"""pulse_harvest_seq015_read_clear_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

def read_pulse(filepath: Path) -> dict | None:
    """Read pulse block from a file. Returns dict or None if no pulse."""
    try:
        text = filepath.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return None
    m = PULSE_RE.search(text)
    if not m:
        return None
    ts_val, hash_val, why_val = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
    state_val = (m.group(4) or '').strip()
    if not state_val:
        state_val = 'pending' if not (ts_val == 'None' and hash_val == 'None') else 'idle'
    if ts_val == 'None' and hash_val == 'None':
        return None  # pulse is blank — no edit recorded
    if state_val != 'pending':
        return None
    return {'edit_ts': ts_val, 'edit_hash': hash_val, 'edit_why': why_val, 'edit_state': state_val}


def clear_pulse(filepath: Path) -> bool:
    """Mark the pulse as harvested while preserving the last metadata."""
    try:
        text = filepath.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return False
    m = PULSE_RE.search(text)
    if not m:
        return False
    ts_val, hash_val, why_val = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
    state_val = (m.group(4) or '').strip()
    if not state_val:
        state_val = 'pending' if not (ts_val == 'None' and hash_val == 'None') else 'idle'
    if state_val == 'harvested':
        return False
    new_text = PULSE_RE.sub(make_pulse_block(ts_val, hash_val, why_val, 'harvested'), text)
    if new_text == text:
        return False
    filepath.write_text(new_text, encoding='utf-8')
    return True
