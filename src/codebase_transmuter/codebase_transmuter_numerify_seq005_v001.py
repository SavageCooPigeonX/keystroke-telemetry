"""codebase_transmuter_numerify_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 29 lines | ~222 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import ast
import re

def numerify_file(filepath):
    try:
        text = filepath.read_text('utf-8', errors='ignore')
        tree = ast.parse(text)
    except Exception:
        return None, {}

    # strip docstrings
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)):
                node.body[0] = ast.Pass()

    numer = _Numerifier()
    tree = numer.visit(tree)
    ast.fix_missing_locations(tree)

    try:
        code = ast.unparse(tree)
    except Exception:
        return None, {}

    return code, numer._map
