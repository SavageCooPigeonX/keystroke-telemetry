"""ast_parser_seq001_v001.py — Parse Python file into function/class map via AST.

Produces: list of functions, classes, top-level constants, with line ranges.
No AI calls. No imports beyond stdlib.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v003 | 82 lines | ~670 tokens
# DESC:   parse_python_file_into_function
# INTENT: desc_upgrade
# LAST:   2026-03-15 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import ast
from pathlib import Path


def parse_file(file_path: str | Path) -> dict:
    """Parse a Python file → structured map of all definitions."""
    source = Path(file_path).read_text(encoding='utf-8')
    tree = ast.parse(source)
    lines = source.split('\n')

    functions, classes, constants = [], [], []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(_extract_func(node, lines))
        elif isinstance(node, ast.ClassDef):
            classes.append(_extract_class(node, lines))
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    constants.append({"name": target.id, "line": node.lineno})

    return {
        "file": str(file_path),
        "total_lines": len(lines),
        "functions": functions,
        "classes": classes,
        "constants": constants,
    }


def _extract_func(node, lines) -> dict:
    """Extract function metadata from AST node."""
    end = node.end_lineno or node.lineno
    decorators = [_decorator_name(d) for d in node.decorator_list]
    return {
        "name": node.name,
        "start_line": node.lineno,
        "end_line": end,
        "line_count": end - node.lineno + 1,
        "is_public": not node.name.startswith('_'),
        "decorators": decorators,
        "is_async": isinstance(node, ast.AsyncFunctionDef),
    }


def _extract_class(node, lines) -> dict:
    """Extract class metadata from AST node."""
    methods = [m.name for m in ast.walk(node)
               if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
               and m is not node]
    bases = [_name_from_node(b) for b in node.bases]
    return {
        "name": node.name,
        "start_line": node.lineno,
        "end_line": node.end_lineno or node.lineno,
        "methods": methods,
        "bases": bases,
    }


def _decorator_name(node) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_name_from_node(node.value)}.{node.attr}"
    if isinstance(node, ast.Call):
        return _decorator_name(node.func)
    return "?"


def _name_from_node(node) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_name_from_node(node.value)}.{node.attr}"
    return "?"
