"""manifest_builder_seq007_signatures_section_seq019_v001.py — Auto-extracted by Pigeon Compiler."""
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
