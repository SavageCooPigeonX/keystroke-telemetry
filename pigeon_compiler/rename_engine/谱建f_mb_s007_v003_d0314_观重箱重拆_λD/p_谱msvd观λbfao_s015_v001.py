"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_build_folder_api_only_seq015_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 015 | VER: v001 | 35 lines | ~350 tokens
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
