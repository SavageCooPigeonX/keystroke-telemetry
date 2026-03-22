"""nametag_seq011_extract_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

def extract_desc_slug(py_path: Path) -> str:
    """Extract a short description slug from a file's docstring.

    Returns snake_case slug like 'filters_live_stream_noise'
    or empty string if no meaningful docstring found.
    """
    try:
        text = py_path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return ''

    first_line = _docstring_first_line(text)
    if not first_line:
        return ''

    return slugify(first_line)
