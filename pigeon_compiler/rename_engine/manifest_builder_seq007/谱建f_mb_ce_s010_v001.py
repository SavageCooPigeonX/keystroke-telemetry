"""manifest_builder_seq007_classes_extract_seq010_v001.py — Auto-extracted by Pigeon Compiler."""
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
