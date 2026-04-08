"""修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc_scan_hardcoded_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import os
import re

def _scan_hardcoded_pigeon_imports(root: Path, registry_paths: set[str] | None = None) -> list[dict]:
    """Find imports that use full pigeon filenames instead of glob patterns.

    Excludes __init__.py (auto-rewritten by pigeon rename engine),
    test helper files, and files tracked in the pigeon registry
    (whose imports are auto-rewritten on commit).
    """
    problems = []
    pat = re.compile(r'(from|import)\s+([\w.]+_seq\d+_v\d+_d\d+__[\w]+)')
    # Also catch relative imports with old long names (no _d but has __)
    pat_rel = re.compile(r'from \.\w+_seq\d+_v\d+(?:_d\d+)?__\w+ import')
    managed = registry_paths or set()
    for py in root.rglob('*.py'):
        if '.git' in py.parts or '__pycache__' in py.parts:
            continue
        rel = str(py.relative_to(root)).replace('\\', '/')
        # Skip auto-managed files
        if py.name == '__init__.py':
            continue
        if py.name.startswith('_test_'):
            continue
        # Skip build artifacts
        if rel.startswith('build/'):
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
