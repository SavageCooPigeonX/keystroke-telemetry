"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_utils_seq017_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 017 | VER: v001 | 55 lines | ~429 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import ast
import re

def _status_icon(line_count: int) -> str:
    if line_count <= MAX_COMPLIANT:
        return '✅'
    elif line_count <= 300:
        return '⚠️ OVER'
    elif line_count <= 500:
        return '🟠 WARN'
    else:
        return '🔴 CRIT'


def _infer_folder_purpose(folder: Path) -> str:
    """Try to get folder purpose from __init__.py docstring or folder name."""
    init = folder / '__init__.py'
    if init.exists():
        try:
            text = init.read_text(encoding='utf-8', errors='ignore')
            tree = ast.parse(text)
            ds = ast.get_docstring(tree)
            if ds:
                return ds.strip().split('\n')[0].strip()
        except Exception:
            pass
    # Fallback: humanize folder name
    name = folder.name.replace('_', ' ').strip()
    return name.capitalize() if name else ''


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
