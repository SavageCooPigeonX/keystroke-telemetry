"""修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_scan_dead_exports_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import ast
import os
import re

def _scan_dead_exports(root: Path, registry: dict) -> list[dict]:
    """Find exported functions that are never imported anywhere."""
    problems = []
    # Build a set of all 'from X import Y' targets across the repo
    import_targets = set()
    call_targets = set()
    for py in root.rglob('*.py'):
        if '.git' in py.parts or '__pycache__' in py.parts:
            continue
        try:
            text = py.read_text(encoding='utf-8')
            tree = ast.parse(text)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.names:
                for alias in node.names:
                    import_targets.add(alias.name)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                call_targets.add(node.func.attr)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                call_targets.add(node.func.id)
    # Also scan vscode-extension/ for dynamic module.func() calls
    ext_dir = root / 'vscode-extension'
    if ext_dir.exists():
        for py in ext_dir.rglob('*.py'):
            try:
                text = py.read_text(encoding='utf-8')
                tree = ast.parse(text)
            except Exception:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    call_targets.add(node.func.attr)
    all_used = import_targets | call_targets

    # Check key src/ modules for unused public functions
    for entry in registry:
        path = entry.get('path', '')
        if not path.startswith('src/') or '/' in path.replace('src/', '', 1):
            continue
        fp = root / path
        if not fp.exists():
            continue
        try:
            tree = ast.parse(fp.read_text(encoding='utf-8'))
        except Exception:
            continue
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith('_') and node.name not in all_used:
                    problems.append({
                        'type': 'dead_export',
                        'file': path,
                        'function': node.name,
                        'line': node.lineno,
                        'severity': 'low',
                        'fix': f'Consider removing or wiring {node.name}() into pipeline',
                    })
    return problems
