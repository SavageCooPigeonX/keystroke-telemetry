"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_build_pigeon_markers_seq014_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 014 | VER: v001 | 40 lines | ~412 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
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
