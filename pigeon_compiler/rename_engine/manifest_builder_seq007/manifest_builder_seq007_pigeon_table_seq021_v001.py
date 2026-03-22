"""manifest_builder_seq007_pigeon_table_seq021_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import ast
import re

def _build_pigeon_table(file_records: list[dict]) -> list[str]:
    """Build the Pigeon Metadata version/token/session table."""
    has_pigeon = any(r['pigeon'] for r in file_records)
    if not has_pigeon:
        return []
    lines = ['| File | Ver | Tokens | Sessions | Last Modified | Intent |',
             '|------|-----|-------:|---------:|---------------|--------|']
    for rec in file_records:
        p = rec['pigeon']
        if not p:
            continue
        short = re.sub(r'_seq\d+.*', '', Path(rec['name']).stem)
        ver = p.get('ver', '?')
        tokens = p.get('tokens', '?')
        sessions = p.get('sessions', '?')
        last = p.get('last', '?')
        intent = p.get('intent', '?')
        lines.append(f'| {short} | {ver} | {tokens} | {sessions} | {last} | {intent} |')
    return lines
