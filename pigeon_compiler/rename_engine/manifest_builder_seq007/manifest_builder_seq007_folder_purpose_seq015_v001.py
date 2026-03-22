"""manifest_builder_seq007_folder_purpose_seq015_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import ast
import re

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
