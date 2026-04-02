"""nametag_seq011_scan_seq008_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 008 | VER: v002 | 37 lines | ~298 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: add_chinese_glyph
# LAST:   2026-04-01 @ aa32a3f
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
import re

def scan_drift(root: Path, folders: list[str] = None) -> list[dict]:
    """Scan all files for name-description drift.

    Returns list of {path, current, suggested, slug_current, slug_new}
    """
    from pigeon_compiler.rename_engine.扫p_sc_s001_v004_d0315_踪稿析_λν import (
        scan_project,
    )

    catalog = scan_project(root, folders)
    drifts = []

    for f in catalog['files']:
        if f['is_init']:
            continue
        # Skip backup/archive files
        if '_BACKUP' in f['stem'] or '_backup' in f['stem']:
            continue
        py = root / f['path']
        if not py.exists():
            continue

        result = detect_drift(py)
        if result['drifted'] and result['docstring_slug']:
            drifts.append({
                'path': f['path'],
                'current': py.name,
                'suggested': result['suggested_name'],
                'slug_current': result['current_slug'],
                'slug_new': result['docstring_slug'],
            })

    return drifts
