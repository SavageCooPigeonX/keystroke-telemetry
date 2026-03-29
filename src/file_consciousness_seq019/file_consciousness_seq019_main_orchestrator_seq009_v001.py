"""file_consciousness_seq019_main_orchestrator_seq009_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import ast
import re

def build_file_consciousness(source_path: Path) -> dict:
    """Derive consciousness profiles for every function in a Python file.

    Returns {functions: [...], meta: {...}} where each function entry
    contains i_am, i_want, i_give, i_fear, i_love — all from AST only.
    """
    source = source_path.read_text(encoding='utf-8', errors='ignore')
    tree = ast.parse(source)

    # Collect all top-level function names for internal call detection
    local_fns = {n.name for n in ast.iter_child_nodes(tree)
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

    profiles = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            profiles.append(_build_func_profile(node, source, local_fns))

    return {
        'file': source_path.name,
        'total_lines': len(source.splitlines()),
        'functions': profiles,
    }
