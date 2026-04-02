"""manifest_builder_seq007_constants_section_seq020_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

def _build_constants_section(file_records: list[dict]) -> list[str]:
    """Build the Constants & Configuration section content."""
    all_consts = []
    for rec in file_records:
        for c in rec['constants']:
            short = re.sub(r'_seq\d+.*', '', Path(rec['name']).stem)
            all_consts.append((short, c['name'], c['value']))
    if not all_consts:
        return []
    lines = ['| Module | Constant | Value |',
             '|--------|----------|-------|']
    for mod, name, val in all_consts:
        val_escaped = val.replace('|', '\\|')
        lines.append(f'| {mod} | `{name}` | `{val_escaped}` |')
    return lines
