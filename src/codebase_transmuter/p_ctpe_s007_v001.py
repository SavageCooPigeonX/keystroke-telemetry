"""codebase_transmuter_seq001_v001_profile_extractor_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v001 | 44 lines | ~413 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import ast
import re

def _extract_file_profile(filepath):
    try:
        text = filepath.read_text('utf-8', errors='ignore')
        tree = ast.parse(text)
    except Exception:
        return None

    lines = text.splitlines()
    imports = [l.strip() for l in lines if l.strip().startswith(('import ', 'from '))]

    funcs = []
    classes = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ''
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)):
                doc = node.body[0].value.value.split('\n')[0].strip()
            args = [a.arg for a in node.args.args if a.arg != 'self']
            funcs.append({'name': node.name, 'args': args, 'doc': doc, 'line': node.lineno})
        elif isinstance(node, ast.ClassDef):
            classes.append({'name': node.name, 'line': node.lineno})

    # first docstring
    module_doc = ''
    if (tree.body and isinstance(tree.body[0], ast.Expr)
            and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)):
        module_doc = tree.body[0].value.value.strip()

    return {
        'lines': len(lines),
        'tokens': _tok(text),
        'imports': imports[:15],
        'functions': funcs,
        'classes': classes,
        'module_doc': module_doc,
        'has_main': any('__main__' in l for l in lines),
    }
