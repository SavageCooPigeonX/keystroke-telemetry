"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_format_signature_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v001 | 46 lines | ~373 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import ast
import re

def _format_signature(node, class_name: str = None) -> str:
    """Format a function AST node into a readable signature string."""
    prefix = 'async ' if isinstance(node, ast.AsyncFunctionDef) else ''
    params = []
    args = node.args

    # Positional args
    defaults_offset = len(args.args) - len(args.defaults)
    for i, arg in enumerate(args.args):
        if arg.arg == 'self' or arg.arg == 'cls':
            continue
        p = arg.arg
        if arg.annotation:
            p += f': {ast.unparse(arg.annotation)}'
        if i >= defaults_offset:
            default = args.defaults[i - defaults_offset]
            try:
                p += f' = {ast.unparse(default)}'
            except Exception:
                p += ' = ...'
        params.append(p)

    # *args and **kwargs
    if args.vararg:
        p = f'*{args.vararg.arg}'
        if args.vararg.annotation:
            p += f': {ast.unparse(args.vararg.annotation)}'
        params.append(p)
    if args.kwarg:
        p = f'**{args.kwarg.arg}'
        if args.kwarg.annotation:
            p += f': {ast.unparse(args.kwarg.annotation)}'
        params.append(p)

    ret = ''
    if node.returns:
        ret = f' -> {ast.unparse(node.returns)}'

    name = node.name
    if class_name:
        name = f'{class_name}.{name}'
    return f'{prefix}def {name}({", ".join(params)}){ret}'
