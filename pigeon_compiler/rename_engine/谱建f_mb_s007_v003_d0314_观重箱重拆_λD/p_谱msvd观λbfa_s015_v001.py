"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_build_folder_api_seq015_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 015 | VER: v001 | 53 lines | ~529 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import ast
import re

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
