"""manifest_builder_seq007_signatures_extract_seq009_v001.py — Auto-extracted by Pigeon Compiler."""
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
