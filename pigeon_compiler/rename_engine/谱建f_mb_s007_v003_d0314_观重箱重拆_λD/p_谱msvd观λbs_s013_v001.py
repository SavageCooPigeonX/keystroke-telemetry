"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_build_sections_seq013_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 013 | VER: v001 | 183 lines | ~1,698 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import ast
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


def _build_folder_api(folder: Path) -> list[str]:
    """Parse __init__.py to list the folder's public re-exports."""
    init = folder / '__init__.py'
    if not init.exists():
        return []
    try:
        text = init.read_text(encoding='utf-8', errors='ignore')
        tree = ast.parse(text)
    except Exception:
        return []
    lines = []
    # Check for __all__
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == '__all__':
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                lines.append(f'- `{elt.value}`')
                    if lines:
                        return lines
    # Fallback: collect ImportFrom names
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.names:
            for alias in node.names:
                name = alias.asname or alias.name
                if not name.startswith('_'):
                    lines.append(f'- `{name}`')
    return lines


def _build_dep_graph(file_records: list[dict], folder: Path) -> list[str]:
    """Build a simple ASCII dependency graph between files in the folder."""
    # Map short stems to file names for intra-folder links
    stem_map = {}
    for rec in file_records:
        short = re.sub(r'_seq\d+.*', '', Path(rec['name']).stem)
        stem_map[short] = rec['name']

    graph_lines = []
    for rec in file_records:
        short_name = re.sub(r'_seq\d+.*', '', Path(rec['name']).stem)
        targets = [d for d in rec['deps'] if d in stem_map and d != short_name]
        if targets:
            arrow_targets = ', '.join(targets)
            graph_lines.append(f'{short_name} --> {arrow_targets}')
    return graph_lines


def _status_icon(line_count: int) -> str:
    if line_count <= MAX_COMPLIANT:
        return '✅'
    elif line_count <= 300:
        return '⚠️ OVER'
    elif line_count <= 500:
        return '🟠 WARN'
    else:
        return '🔴 CRIT'


def _infer_folder_purpose(folder: Path) -> str:
    """Try to get folder purpose from __init__.py docstring or folder name."""
    init = folder / '__init__.py'
    if init.exists():
        try:
            text = init.read_text(encoding='utf-8', errors='ignore')
            tree = ast.parse(text)
            ds = ast.get_docstring(tree)
            if ds:
                return ds.strip().split('\n')[0].strip()
        except Exception:
            pass
    # Fallback: humanize folder name
    name = folder.name.replace('_', ' ').strip()
    return name.capitalize() if name else ''


def _parse_existing_notes(manifest_path: Path) -> dict:
    """Parse existing MANIFEST.md to preserve Notes column values.

    Returns {filename: notes_text} for any file that has notes.
    """
    notes = {}
    if not manifest_path.exists():
        return notes
    try:
        text = manifest_path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return notes
    for line in text.splitlines():
        if not line.startswith('|'):
            continue
        cols = [c.strip() for c in line.split('|')]
        if len(cols) < 8:  # |seq|file|lines|status|desc|notes|
            continue
        fname = cols[2]
        if fname.endswith('.py') and cols[6]:
            notes[fname] = cols[6]
    return notes
