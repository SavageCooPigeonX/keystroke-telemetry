"""manifest_builder_seq007_constants_extract_seq011_v001.py — Auto-extracted by Pigeon Compiler."""
import ast
import re

def _extract_constants(text: str) -> list[dict]:
    """Extract module-level public constants with their values."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    consts = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id.isupper():
                    try:
                        val_str = ast.unparse(node.value)
                        if len(val_str) > 80:
                            val_str = val_str[:77] + '...'
                    except Exception:
                        val_str = '...'
                    consts.append({'name': t.id, 'value': val_str})
    return consts
