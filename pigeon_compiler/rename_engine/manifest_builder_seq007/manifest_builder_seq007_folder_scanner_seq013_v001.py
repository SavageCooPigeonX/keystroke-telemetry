"""manifest_builder_seq007_folder_scanner_seq013_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

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
