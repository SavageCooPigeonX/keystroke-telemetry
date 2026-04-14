"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_extract_signatures_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v001 | 69 lines | ~588 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import ast
import re

def _extract_signatures(text: str) -> list[str]:
    """Extract public function signatures with type hints."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    sigs = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith('_'):
                continue
            sig = _format_signature(node)
            sigs.append(sig)
        elif isinstance(node, ast.ClassDef):
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if item.name.startswith('_') and item.name != '__init__':
                        continue
                    sig = _format_signature(item, class_name=node.name)
                    sigs.append(sig)
    return sigs


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
