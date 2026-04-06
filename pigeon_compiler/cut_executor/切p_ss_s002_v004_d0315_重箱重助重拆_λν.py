"""source_slicer_seq002_v001.py — Extract functions/constants from source via AST.

Given a list of names, extracts the exact source lines for each one.
Returns a dict {name: source_lines_str} ready for writing.
"""

import ast
from pathlib import Path


def slice_source(file_path: str | Path, names: list[str]) -> dict:
    """Return {name: source_code_str} for each requested name."""
    source = Path(file_path).read_text(encoding='utf-8')
    lines = source.splitlines(keepends=True)
    tree = ast.parse(source)
    result = {}
    for node in ast.iter_child_nodes(tree):
        name = _node_name(node)
        if name and name in names:
            start, end = _node_range(node, lines)
            result[name] = "".join(lines[start:end])
    return result


def _node_name(node) -> str | None:
    """Get the name of a top-level definition or assignment."""
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return node.name
    if isinstance(node, ast.ClassDef):
        return node.name
    if isinstance(node, ast.Assign):
        for t in node.targets:
            if isinstance(t, ast.Name):
                return t.id
    return None


def _node_range(node, lines: list) -> tuple[int, int]:
    """Return (start_idx, end_idx) including decorators + trailing blank."""
    start = node.lineno - 1
    # Include decorators above function/class
    if hasattr(node, 'decorator_list') and node.decorator_list:
        start = node.decorator_list[0].lineno - 1
    end = (node.end_lineno or node.lineno)
    # Include one trailing blank line if present
    if end < len(lines) and lines[end].strip() == '':
        end += 1
    return start, end
