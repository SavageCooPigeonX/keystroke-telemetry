"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_extract_docstring_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 29 lines | ~284 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import ast
import re

def _extract_docstring_first_line(text: str, filename: str) -> str:
    """Extract the first line of the module docstring."""
    try:
        tree = ast.parse(text)
        ds = ast.get_docstring(tree)
        if ds:
            first = ds.strip().split('\n')[0].strip()
            # If docstring starts with "filename.py — description",
            # extract just the description (the intent)
            if ' — ' in first:
                first = first.split(' — ', 1)[1].strip()
            elif ' - ' in first:
                parts = first.split(' - ', 1)
                if len(parts[0].split()) <= 4:
                    first = parts[1].strip()
            if len(first) > 80:
                first = first[:77] + '...'
            return first
    except SyntaxError:
        pass
    # Fallback: infer from filename
    stem = Path(filename).stem
    clean = re.sub(r'_seq\d+_v\d+', '', stem).replace('_', ' ').strip()
    return clean.capitalize() if clean else filename
