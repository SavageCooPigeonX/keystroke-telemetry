"""self_fix_seq013_scan_hardcoded_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import os
import re

def _scan_hardcoded_pigeon_imports(root: Path, registry_paths: set[str] | None = None) -> list[dict]:
    """Find imports that use full pigeon filenames instead of glob patterns.

    Excludes __init__.py (auto-rewritten by pigeon rename engine),
    pigeon_compiler/ internals (managed by the compiler itself),
    test helper files, and files tracked in the pigeon registry
    (whose imports are auto-rewritten on commit).
    """
    problems = []
    pat = re.compile(r'(from|import)\s+([\w.]+_seq\d+_v\d+_d\d+__[\w]+)')
    managed = registry_paths or set()
    for py in root.rglob('*.py'):
        if '.git' in py.parts or '__pycache__' in py.parts:
            continue
        rel = str(py.relative_to(root)).replace('\\', '/')
        # Skip auto-managed files
        if py.name == '__init__.py':
            continue
        if rel.startswith('pigeon_compiler/'):
            continue
        if py.name.startswith('_test_'):
            continue
        # Files tracked by pigeon have their imports auto-rewritten
        if rel in managed:
            continue
        try:
            text = py.read_text(encoding='utf-8')
        except Exception:
            continue
        for m in pat.finditer(text):
            problems.append({
                'type': 'hardcoded_import',
                'file': rel,
                'line': text[:m.start()].count('\n') + 1,
                'import': m.group(2),
                'severity': 'critical',
                'fix': f'Use glob-based dynamic import instead of hardcoded name',
            })
    return problems
