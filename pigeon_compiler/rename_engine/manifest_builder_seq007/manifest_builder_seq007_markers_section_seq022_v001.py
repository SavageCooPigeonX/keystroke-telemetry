"""manifest_builder_seq007_markers_section_seq022_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

def _build_markers_section(file_records: list[dict]) -> list[str]:
    """Build the Code Markers section for TODO/FIXME/HACK."""
    all_markers = []
    for rec in file_records:
        for m in rec['markers']:
            short = re.sub(r'_seq\d+.*', '', Path(rec['name']).stem)
            all_markers.append((short, m['tag'], m['line'], m['text']))
    if not all_markers:
        return ['*No TODO/FIXME/HACK markers found — codebase is clean.*']
    lines = ['| Module | Tag | Line | Note |',
             '|--------|-----|-----:|------|']
    for mod, tag, ln, txt in all_markers:
        lines.append(f'| {mod} | {tag} | {ln} | {txt} |')
    return lines
