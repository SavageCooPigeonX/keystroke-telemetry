"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_extract_classes_seq009_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v001 | 31 lines | ~302 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import ast
import re

def _extract_classes(text: str) -> list[dict]:
    """Extract class definitions with methods and bases."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    classes = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
            bases = [ast.unparse(b) for b in node.bases] if node.bases else []
            decorators = []
            for d in node.decorator_list:
                try:
                    decorators.append(ast.unparse(d))
                except Exception:
                    pass
            methods = [m.name for m in node.body
                       if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                       and not m.name.startswith('_')]
            classes.append({
                'name': node.name,
                'bases': bases,
                'decorators': decorators,
                'methods': methods,
                'lines': (node.end_lineno or node.lineno) - node.lineno + 1,
            })
    return classes
