"""self_fix_seq013_scan_duplicate_docstrings_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

def _scan_duplicate_docstrings(root: Path, registry: dict) -> list[dict]:
    """Find files with duplicated docstring blocks."""
    problems = []
    for entry in registry:
        fp = root / entry['path']
        if not fp.exists():
            continue
        try:
            lines = fp.read_text(encoding='utf-8').splitlines()
        except Exception:
            continue
        if len(lines) < 20:
            continue
        # Check if first non-empty content block appears again later
        doc_end = 0
        for i, ln in enumerate(lines):
            if ln.strip().startswith('"""') and i > 0:
                doc_end = i + 1
                break
        if doc_end < 3:
            continue
        doc_text = '\n'.join(lines[:doc_end]).strip()
        rest = '\n'.join(lines[doc_end:])
        if doc_text in rest:
            problems.append({
                'type': 'duplicate_docstring',
                'file': entry['path'],
                'severity': 'medium',
                'fix': 'Remove duplicated docstring block',
            })
    return problems
