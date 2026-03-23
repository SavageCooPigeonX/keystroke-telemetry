"""pulse_harvest_seq015_inject_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

def inject_pulse(filepath: Path) -> bool:
    """Add a blank pulse block after the pigeon prompt box (or after docstring)."""
    try:
        text = filepath.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError):
        return False
    if PULSE_RE.search(text):
        return False  # already has one
    # Insert after pigeon prompt box if present
    pigeon_box = re.search(
        r'^# ── pigeon ─[^\n]*\n(?:# [^\n]*\n)*# ─{10,}─*\n',
        text, re.MULTILINE,
    )
    if pigeon_box:
        pos = pigeon_box.end()
        new_text = text[:pos] + PULSE_BLOCK + '\n' + text[pos:]
    else:
        # Insert after module docstring
        ds = re.match(r'^("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')\n', text)
        if ds:
            pos = ds.end()
            new_text = text[:pos] + PULSE_BLOCK + '\n' + text[pos:]
        else:
            new_text = PULSE_BLOCK + '\n' + text
    filepath.write_text(new_text, encoding='utf-8')
    return True


def inject_all_pulses(root: Path) -> int:
    """Add blank pulse blocks to all src/*.py files that lack one."""
    count = 0
    src = root / 'src'
    if not src.is_dir():
        return 0
    for py in src.glob('*.py'):
        if py.name.startswith('__'):
            continue
        if inject_pulse(py):
            count += 1
    return count
