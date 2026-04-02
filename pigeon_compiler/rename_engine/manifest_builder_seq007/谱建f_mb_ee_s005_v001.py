"""manifest_builder_seq007_exports_extract_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
import ast
import re

def _extract_exports(text: str) -> list[str]:
    """Extract public class/function/constant names from a module."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    names = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
            names.append(node.name)
        elif isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
            names.append(f'{node.name}()')
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = []
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif node.target:
                targets = [node.target]
            for t in targets:
                if isinstance(t, ast.Name) and t.id.isupper():
                    names.append(t.id)
    return names
