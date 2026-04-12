"""修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_scan_hardcoded_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import ast
import os
import re

def _scan_hardcoded_pigeon_imports(root: Path, registry_paths: set[str] | None = None) -> list[dict]:
    """Find imports that use full pigeon filenames instead of glob patterns.

    Excludes __init__.py (auto-rewritten by pigeon rename engine),
    test helper files, and files tracked in the pigeon registry
    (whose imports are auto-rewritten on commit).
    Skips matches inside docstrings and comments (false positives).
    """
    problems = []
    pat = re.compile(r'(from|import)\s+([\w.]+_seq\d+_v\d+_d\d+__[\w]+)')
    managed = registry_paths or set()
    for py in root.rglob('*.py'):
        if '.git' in py.parts or '__pycache__' in py.parts:
            continue
        rel = str(py.relative_to(root)).replace('\\', '/')
        if py.name == '__init__.py':
            continue
        if py.name.startswith('_test_'):
            continue
        if rel.startswith('build/'):
            continue
        if rel in managed:
            continue
        try:
            text = py.read_text(encoding='utf-8')
        except Exception:
            continue
        # Build set of line numbers that are inside string literals or comments
        skip_lines = _non_code_lines(text)
        for m in pat.finditer(text):
            line_num = text[:m.start()].count('\n') + 1
            if line_num in skip_lines:
                continue
            problems.append({
                'type': 'hardcoded_import',
                'file': rel,
                'line': line_num,
                'import': m.group(2),
                'severity': 'critical',
                'fix': 'Use glob-based dynamic import instead of hardcoded name',
            })
    return problems


def _non_code_lines(source: str) -> set[int]:
    """Return line numbers occupied by comments or string literals."""
    skip = set()
    # Comments
    for i, line in enumerate(source.splitlines(), 1):
        stripped = line.lstrip()
        if stripped.startswith('#'):
            skip.add(i)
    # String literals (docstrings, multi-line strings) via AST
    try:
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Expr) and isinstance(node.value, (ast.Constant,)):
                if isinstance(node.value.value, str):
                    for ln in range(node.lineno, node.end_lineno + 1):
                        skip.add(ln)
    except SyntaxError:
        pass
    return skip
