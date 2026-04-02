"""pulse_harvest_seq015_stamp_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
import re

def stamp_pulse(filepath: Path, edit_why: str = 'auto') -> bool:
    """Stamp the pulse block with current time + content hash."""
    try:
        text = filepath.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return False
    if not PULSE_RE.search(text):
        return False
    ts = datetime.now(timezone.utc).isoformat()
    h = content_hash(text)
    new_block = make_pulse_block(ts, h, edit_why, 'pending')
    new_text = PULSE_RE.sub(new_block, text)
    filepath.write_text(new_text, encoding='utf-8')
    return True
