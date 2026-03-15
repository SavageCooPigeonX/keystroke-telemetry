"""scanner_seq001_v001.py — Walk the project tree and catalog all Python modules.

Returns a structured map of every .py file with its module path,
line count, and whether it already follows Pigeon Code naming.
"""
import re
from pathlib import Path

PIGEON_PATTERN = re.compile(r'^.+_seq\d{3}_v\d{3}(_d\d{4})?(__[a-z0-9_]+)?\.py$')
PIGEON_CONTAINS = re.compile(r'_seq\d{3}_v\d{3}')
SKIP_DIRS = {'.venv', '__pycache__', 'node_modules', '.git', '.github',
             '_llm_tests_put_all_test_and_debug_scripts_here',
             '.next', 'compiler_output', 'cache', '.pytest_cache',
             'audit_backups', 'json_uploads', 'logs', 'rollback_logs',
             '.vscode'}
SKIP_FILES = {'__init__.py', 'conftest.py', 'app.py', 'manage.py', 'wsgi.py',
              'Procfile', 'Dockerfile', 'Makefile',
              'requirements.txt', 'setup.py', 'setup.cfg', 'pyproject.toml',
              'railway.json', 'railway.toml', 'railway.worker.json',
              'nixpacks.toml', 'docker-compose.yml', 'docker-compose.yaml'}


def scan_project(root: Path, folders: list[str] = None) -> dict:
    """Scan project and return file catalog.

    Args:
        root: project root directory
        folders: optional list of folder names to scope (e.g. ['api', 'consensus'])
                 None = scan everything
    Returns:
        dict with 'files' list and 'stats' summary
    """
    root = Path(root)
    files = []
    for py in sorted(root.rglob('*.py')):
        if _should_skip(py, root):
            continue
        if folders:
            try:
                rel = py.relative_to(root)
                rel_str = str(rel).replace('\\', '/')
                if not any(rel_str.startswith(f + '/') or rel_str.startswith(f.rstrip('/') + '/')
                           for f in folders):
                    # Also check top-level folder for backward compat
                    top = rel.parts[0] if len(rel.parts) > 1 else None
                    if top not in folders:
                        continue
            except ValueError:
                continue
        files.append(_catalog_file(py, root))

    compliant = sum(1 for f in files if f['is_pigeon'])
    return {
        'files': files,
        'stats': {
            'total': len(files),
            'compliant': compliant,
            'non_compliant': len(files) - compliant,
            'compliance_pct': round(compliant / max(len(files), 1) * 100, 1),
        }
    }


def _catalog_file(py: Path, root: Path) -> dict:
    rel = py.relative_to(root)
    module_path = str(rel.with_suffix('')).replace('\\', '.').replace('/', '.')
    folder = str(rel.parent).replace('\\', '/') if len(rel.parts) > 1 else ''
    lines = _count_lines(py)
    return {
        'path': str(rel).replace('\\', '/'),
        'folder': folder,
        'stem': py.stem,
        'module_path': module_path,
        'lines': lines,
        'is_pigeon': bool(PIGEON_PATTERN.match(py.name) or PIGEON_CONTAINS.search(py.stem)),
        'is_init': py.name == '__init__.py',
    }


def _count_lines(py: Path) -> int:
    try:
        return len(py.read_text(encoding='utf-8', errors='ignore').splitlines())
    except Exception:
        return 0


def _should_skip(py: Path, root: Path) -> bool:
    parts = py.relative_to(root).parts
    for p in parts:
        if p in SKIP_DIRS:
            return True
        # Skip any .venv variant (.venv-1, .venv-old, etc.)
        if p.startswith('.venv'):
            return True
        # Skip _llm_tests* variants
        if p.startswith('_llm_tests'):
            return True
    if py.name in SKIP_FILES:
        return True
    return False
