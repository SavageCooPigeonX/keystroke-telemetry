"""manifest_builder_seq007_existing_notes_seq016_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

def _parse_existing_notes(manifest_path: Path) -> dict:
    """Parse existing MANIFEST.md to preserve Notes column values.

    Returns {filename: notes_text} for any file that has notes.
    """
    notes = {}
    if not manifest_path.exists():
        return notes
    try:
        text = manifest_path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return notes
    for line in text.splitlines():
        if not line.startswith('|'):
            continue
        cols = [c.strip() for c in line.split('|')]
        if len(cols) < 8:  # |seq|file|lines|status|desc|notes|
            continue
        fname = cols[2]
        if fname.endswith('.py') and cols[6]:
            notes[fname] = cols[6]
    return notes
