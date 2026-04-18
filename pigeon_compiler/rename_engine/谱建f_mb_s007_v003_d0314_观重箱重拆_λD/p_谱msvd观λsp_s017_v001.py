"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_status_purpose_seq017_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 017 | VER: v001 | 31 lines | ~245 tokens
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
