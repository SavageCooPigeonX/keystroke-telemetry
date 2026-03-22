"""nametag_seq011_detect_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

def detect_drift(py_path: Path) -> dict:
    """Check if a file's name-description matches its docstring.

    Returns {drifted: bool, current_slug: str, docstring_slug: str,
             suggested_name: str}
    """
    parsed = parse_nametag(py_path.name)
    current_slug = parsed['desc_slug']
    docstring_slug = extract_desc_slug(py_path)

    if not docstring_slug:
        return {'drifted': False, 'current_slug': current_slug,
                'docstring_slug': '', 'suggested_name': py_path.name}

    drifted = current_slug != docstring_slug
    suggested = build_nametag(parsed['base_stem'], docstring_slug)

    return {
        'drifted': drifted,
        'current_slug': current_slug,
        'docstring_slug': docstring_slug,
        'suggested_name': suggested,
    }
