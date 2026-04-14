"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_build_signatures_constants_seq013_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 013 | VER: v001 | 43 lines | ~439 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import re

def _build_signatures_section(file_records: list[dict]) -> list[str]:
    """Build the Module Signatures section content."""
    lines = []
    for rec in file_records:
        if not rec['signatures'] and not rec['classes']:
            continue
        short = re.sub(r'_seq\d+.*', '', Path(rec['name']).stem)
        lines.append(f'**{short}**')
        lines.append('```python')
        for cls in rec['classes']:
            deco_parts = [f'@{d}' for d in cls['decorators']]
            bases_str = f'({", ".join(cls["bases"])})' if cls['bases'] else ''
            for dp in deco_parts:
                lines.append(dp)
            lines.append(f'class {cls["name"]}{bases_str}:  # {cls["lines"]} lines')
            if cls['methods']:
                lines.append(f'    # methods: {", ".join(cls["methods"])}')
        for sig in rec['signatures']:
            lines.append(sig)
        lines.append('```')
        lines.append('')
    return lines


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
