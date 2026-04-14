"""module_identity_code_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import ast
import re

def _extract_code_skeleton(root: Path, path: str, name: str = '', seq: int = 0) -> dict:
    """Extract function signatures, imports, classes, and docstring from source."""
    empty = {'functions': [], 'imports': [], 'classes': [], 'docstring': '', 'line_count': 0}
    fpath = root / path
    if not fpath.exists():
        # Registry path stale (pigeon rename drift) — search by seq pattern
        parent = (root / path).parent if path else root / 'src'
        if parent.is_dir():
            # Try seq-based match first (most reliable across renames)
            seq_tag = f'_s{seq:03d}_' if seq else ''
            candidates = []
            for f in parent.iterdir():
                if f.suffix != '.py':
                    continue
                if seq_tag and seq_tag in f.stem:
                    candidates.append(f)
                elif name and name in f.stem:
                    candidates.append(f)
            if candidates:
                fpath = max(candidates, key=lambda f: f.stat().st_mtime)
    if not fpath.exists():
        return empty
    try:
        src = fpath.read_text('utf-8', errors='replace')
    except Exception:
        return empty

    line_count = src.count('\n') + 1
    functions = []
    imports = []
    classes = []
    docstring = ''

    try:
        tree = ast.parse(src)
    except SyntaxError:
        return {'functions': [], 'imports': [], 'classes': [], 'docstring': '', 'line_count': line_count}

    # Module docstring
    if (tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)):
        docstring = tree.body[0].value.value.strip()[:300]

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = [a.arg for a in node.args.args]
            fn_doc = ast.get_docstring(node) or ''
            functions.append({
                'name': node.name,
                'args': args,
                'line': node.lineno,
                'doc': fn_doc[:150],
            })
        elif isinstance(node, ast.ClassDef):
            methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
            classes.append({'name': node.name, 'methods': methods, 'line': node.lineno})
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ''
                names = [a.name for a in node.names]
                imports.append(f'from {mod} import {", ".join(names)}')
            else:
                imports.append(f'import {", ".join(a.name for a in node.names)}')

    # Truncate raw source for rendering (max ~8000 chars)
    source_text = src[:8000] if len(src) > 8000 else src

    return {
        'functions': functions[:30],
        'imports': imports[:20],
        'classes': classes[:10],
        'docstring': docstring,
        'line_count': line_count,
        'source': source_text,
    }
