"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_extract_exports_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 26 lines | ~252 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import ast
import re

def _extract_exports(text: str) -> list[str]:
    """Extract public class/function/constant names from a module."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    names = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
            names.append(node.name)
        elif isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
            names.append(f'{node.name}()')
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = []
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif node.target:
                targets = [node.target]
            for t in targets:
                if isinstance(t, ast.Name) and t.id.isupper():
                    names.append(t.id)
    return names
