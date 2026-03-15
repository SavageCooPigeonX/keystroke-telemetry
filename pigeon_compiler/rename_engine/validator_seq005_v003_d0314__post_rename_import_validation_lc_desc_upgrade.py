"""validator_seq005_v001.py — Post-rename import validation.

Scans every .py file, parses import statements,
checks that every internal import resolves to an existing file.
"""
import ast
import re
from pathlib import Path

SKIP_DIRS = {'.venv', '__pycache__', 'node_modules', '.git',
             '_llm_tests_put_all_test_and_debug_scripts_here',
             '.next', '.pytest_cache', 'compiler_output'}

KNOWN_INTERNAL = {'config', 'integrations', 'storage_maif', 'models',
                  'auth', 'consensus', 'delivery', 'harvester', 'runner',
                  'production_auditor', 'pigeon_compiler', 'maif_whisperer',
                  'maif_propaganda', 'api', 'directory', 'users', 'middleware',
                  'drift_tracker', 'listen', 'deepseek_db', 'scripts',
                  'documentation', 'research_team', 'main', 'frontend'}


def validate_imports(root: Path) -> dict:
    """Validate all internal imports resolve to existing files.

    Returns dict with 'valid' bool, 'broken' list, 'total_checked' int.
    """
    root = Path(root)
    broken = []
    total = 0

    for py in sorted(root.rglob('*.py')):
        if _should_skip(py, root):
            continue
        text = _safe_read(py)
        if not text:
            continue
        rel = str(py.relative_to(root)).replace('\\', '/')
        imports = _extract_imports(text)
        for imp in imports:
            if not _is_internal(imp['module']):
                continue
            total += 1
            if not _resolves(root, imp['module']):
                broken.append({
                    'file': rel,
                    'line': imp['line'],
                    'import': imp['raw'],
                    'module': imp['module'],
                })

    return {
        'valid': len(broken) == 0,
        'broken': broken,
        'total_checked': total,
    }


def _extract_imports(text: str) -> list:
    results = []
    for i, line in enumerate(text.split('\n'), 1):
        s = line.strip()
        if s.startswith('from '):
            m = re.match(r'from\s+([\w.]+)\s+import', s)
            if m:
                results.append({'module': m.group(1), 'line': i, 'raw': s})
        elif s.startswith('import '):
            m = re.match(r'import\s+([\w.]+)', s)
            if m:
                results.append({'module': m.group(1), 'line': i, 'raw': s})
    return results


def _is_internal(module: str) -> bool:
    top = module.split('.')[0]
    return top in KNOWN_INTERNAL


def _resolves(root: Path, module: str) -> bool:
    parts = module.split('.')
    # Check as file: a.b.c → a/b/c.py
    file_path = root / '/'.join(parts)
    if file_path.with_suffix('.py').exists():
        return True
    # Check as package: a.b.c → a/b/c/__init__.py
    if (file_path / '__init__.py').exists():
        return True
    # Check parent package with init: a.b → a/b/__init__.py
    if len(parts) >= 2:
        parent = root / '/'.join(parts[:-1])
        if (parent / '__init__.py').exists():
            init_text = _safe_read(parent / '__init__.py')
            if parts[-1] in init_text:
                return True
    return False


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        return ''


def _should_skip(py: Path, root: Path) -> bool:
    parts = py.relative_to(root).parts
    return any(p in SKIP_DIRS for p in parts)
