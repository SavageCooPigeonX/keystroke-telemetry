"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_scan_folder_seq012_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 012 | VER: v001 | 38 lines | ~344 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import re

from .p_谱msvd观λc_s001_v001 import SKIP_FILES
from .p_谱msvd观λse_s002_v001 import (
    _extract_classes,
    _extract_code_markers,
    _extract_constants,
    _extract_deps,
    _extract_docstring_first_line,
    _extract_exports,
    _extract_seq,
    _extract_signatures,
    _parse_pigeon_header,
)

def _scan_folder_rich(folder: Path) -> list[dict]:
    """Return list of file records with exports, deps, signatures, and pigeon metadata."""
    results = []
    for py in sorted(folder.glob('*.py')):
        if py.name in SKIP_FILES:
            continue
        try:
            text = py.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        lc = len(text.splitlines())
        desc = _extract_docstring_first_line(text, py.name)
        exports = _extract_exports(text)
        deps = _extract_deps(text, folder.name)
        seq = _extract_seq(py.name) or f'{len(results)+1:03d}'
        pigeon = _parse_pigeon_header(text)
        signatures = _extract_signatures(text)
        classes = _extract_classes(text)
        constants = _extract_constants(text)
        markers = _extract_code_markers(text)
        results.append({
            'name': py.name,
            'lines': lc,
            'desc': desc,
            'exports': exports,
            'deps': deps,
            'seq': seq,
            'pigeon': pigeon,
            'signatures': signatures,
            'classes': classes,
            'constants': constants,
            'markers': markers,
        })
    return results
