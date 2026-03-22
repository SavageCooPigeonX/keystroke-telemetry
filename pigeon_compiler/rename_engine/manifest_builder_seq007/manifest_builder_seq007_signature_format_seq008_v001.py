"""manifest_builder_seq007_signature_format_seq008_v001.py — Auto-extracted by Pigeon Compiler."""
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
