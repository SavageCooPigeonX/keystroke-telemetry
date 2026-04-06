"""shared_state_detector_seq004_v001.py — Detect module-level shared state.

Finds: module-level variables, mutable assignments, global constants,
and which functions READ those names. Shared state = resistance to splitting.
"""

import ast
from pathlib import Path


def detect_shared_state(file_path: str | Path) -> dict:
    """Return module-level names and which functions reference them."""
    source = Path(file_path).read_text(encoding='utf-8')
    tree = ast.parse(source)

    # 1. Collect module-level names (assignments, not inside functions)
    module_names = {}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    module_names[t.id] = {
                        "line": node.lineno, "is_const": t.id.isupper(),
                        "used_by": []
                    }
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            module_names[node.target.id] = {
                "line": node.lineno, "is_const": node.target.id.isupper(),
                "used_by": []
            }

    # 2. For each function, check which module-level names it reads
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            refs = _collect_name_refs(node)
            for name in refs:
                if name in module_names:
                    module_names[name]["used_by"].append(node.name)

    return module_names


def compute_coupling_score(shared: dict) -> float:
    """0.0 = no shared state, 1.0 = everything coupled."""
    if not shared:
        return 0.0
    mutable = [s for s in shared.values() if not s["is_const"]]
    widely_used = [s for s in shared.values() if len(s["used_by"]) > 2]
    score = min(1.0, (len(mutable) * 0.2 + len(widely_used) * 0.15))
    return round(score, 2)


def _collect_name_refs(func_node) -> set:
    """Collect all Name references inside a function body."""
    names = set()
    for node in ast.walk(func_node):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            names.add(node.id)
    return names
