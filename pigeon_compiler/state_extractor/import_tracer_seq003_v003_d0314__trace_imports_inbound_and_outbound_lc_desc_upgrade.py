"""import_tracer_seq003_v001.py — Trace imports inbound and outbound.

Outbound: what this file imports (stdlib, pip, internal project modules).
Inbound: which OTHER project files import from this file.
"""
import ast
import re
from pathlib import Path


def trace_outbound(file_path: str | Path) -> list[dict]:
    """Return all imports in the file with classification."""
    source = Path(file_path).read_text(encoding='utf-8')
    tree = ast.parse(source)
    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({"module": alias.name, "names": [alias.asname or alias.name],
                                "line": node.lineno, "kind": _classify(alias.name)})
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            names = [a.name for a in node.names]
            imports.append({"module": mod, "names": names,
                            "line": node.lineno, "kind": _classify(mod)})
    return imports


def trace_inbound(file_path: str | Path, project_root: str | Path) -> list[dict]:
    """Scan project for files that import from this file."""
    fp = Path(file_path)
    root = Path(project_root)
    # Build the module path this file represents
    try:
        rel = fp.relative_to(root).with_suffix('')
        module_str = str(rel).replace('\\', '/').replace('/', '.')
    except ValueError:
        return []

    stem = fp.stem  # e.g. "folder_auditor"
    results = []
    for py in root.rglob('*.py'):
        if py == fp or '__pycache__' in str(py) or '.venv' in str(py):
            continue
        try:
            text = py.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        if module_str in text or stem in text:
            # Verify it's an actual import line
            for m in re.finditer(r'^(?:from|import)\s+.*' + re.escape(stem), text, re.M):
                results.append({"file": str(py.relative_to(root)), "line": text[:m.start()].count('\n') + 1,
                                "match": m.group().strip()})
                break  # one match per file is enough
    return results


def _classify(module: str) -> str:
    """Classify import as stdlib, external, or internal."""
    KNOWN_INTERNAL = {'config', 'integrations', 'storage_maif', 'models',
                      'auth', 'consensus', 'delivery', 'harvester', 'runner',
                      'production_auditor', 'pigeon_compiler', 'maif_whisperer',
                      'maif_propaganda', 'api', 'directory', 'users', 'middleware',
                      'drift_auditor', 'listen', 'deepseek_db', 'scripts'}
    top = module.split('.')[0] if module else ''
    if top in KNOWN_INTERNAL:
        return 'internal'
    try:
        __import__(top)
        return 'stdlib'
    except ImportError:
        return 'external'
