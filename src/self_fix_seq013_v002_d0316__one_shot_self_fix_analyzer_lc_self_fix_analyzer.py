"""One-shot self-fix analyzer: cross-file problem detection + targeted resolution."""

# ── pigeon ────────────────────────────────────
# SEQ: 013 | VER: v002 | 339 lines | ~3,117 tokens
# DESC:   one_shot_self_fix_analyzer
# INTENT: self_fix_analyzer
# LAST:   2026-03-16 @ c8de77c
# SESSIONS: 1
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# ── /pulse ──

import ast
import json
import os
import re
import urllib.request
from pathlib import Path


# ── Problem detectors ─────────────────────────────────────────────────────────

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


def _scan_duplicate_docstrings(root: Path, registry: dict) -> list[dict]:
    """Find files with duplicated docstring blocks."""
    problems = []
    for entry in registry:
        fp = root / entry['path']
        if not fp.exists():
            continue
        try:
            lines = fp.read_text(encoding='utf-8').splitlines()
        except Exception:
            continue
        if len(lines) < 20:
            continue
        # Check if first non-empty content block appears again later
        doc_end = 0
        for i, ln in enumerate(lines):
            if ln.strip().startswith('"""') and i > 0:
                doc_end = i + 1
                break
        if doc_end < 3:
            continue
        doc_text = '\n'.join(lines[:doc_end]).strip()
        rest = '\n'.join(lines[doc_end:])
        if doc_text in rest:
            problems.append({
                'type': 'duplicate_docstring',
                'file': entry['path'],
                'severity': 'medium',
                'fix': 'Remove duplicated docstring block',
            })
    return problems


def _scan_cross_file_coupling(root: Path, registry: dict) -> list[dict]:
    """Build import graph and find high-coupling modules."""
    import_graph: dict[str, set] = {}  # file -> set of files it imports from
    name_to_path: dict[str, str] = {}  # module stem -> registry path

    for entry in registry:
        stem = Path(entry['path']).stem
        # Strip pigeon metadata to get base module name
        base = re.sub(r'_seq\d+.*$', '', stem)
        name_to_path[base] = entry['path']
        name_to_path[stem] = entry['path']

    for entry in registry:
        fp = root / entry['path']
        if not fp.exists():
            continue
        try:
            tree = ast.parse(fp.read_text(encoding='utf-8'))
        except Exception:
            continue
        deps = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                # Extract the leaf module name
                parts = node.module.split('.')
                leaf = parts[-1]
                base_leaf = re.sub(r'_seq\d+.*$', '', leaf)
                target = name_to_path.get(leaf) or name_to_path.get(base_leaf)
                if target and target != entry['path']:
                    deps.add(target)
        import_graph[entry['path']] = deps

    # Find files with high fan-in (many dependents)
    fan_in: dict[str, int] = {}
    for src_file, deps in import_graph.items():
        for dep in deps:
            fan_in[dep] = fan_in.get(dep, 0) + 1

    problems = []
    for path, count in sorted(fan_in.items(), key=lambda x: -x[1]):
        if count >= 5:
            problems.append({
                'type': 'high_coupling',
                'file': path,
                'fan_in': count,
                'severity': 'info',
                'fix': f'Module has {count} dependents — changes here break many files',
            })

    return problems, import_graph


def _scan_query_noise(root: Path) -> list[dict]:
    """Detect poisoned query_memory entries."""
    problems = []
    qm_path = root / 'query_memory.json'
    if not qm_path.exists():
        return problems
    try:
        raw = json.loads(qm_path.read_text('utf-8'))
        entries = raw.get('entries', raw.get('queries', []))
        noise = [e for e in entries
                 if isinstance(e, dict) and '(background)' in str(e.get('text', e.get('query_text', '')))]
        if noise:
            problems.append({
                'type': 'query_noise',
                'count': len(noise),
                'severity': 'high',
                'fix': 'Filter "(background)" queries in extension flush — use active filename instead',
            })
    except Exception:
        pass
    return problems


# ── Main analyzer ─────────────────────────────────────────────────────────────

def run_self_fix(
    root: Path,
    registry: dict,
    changed_py: list[str] | None = None,
    intent: str = '',
) -> dict:
    """One-shot cross-file analysis. Returns problem report dict.

    Does NOT loop or auto-fix — produces a report with targeted resolutions.
    """
    reg_list = registry if isinstance(registry, list) else list(registry.values())
    if isinstance(registry, dict) and 'files' in registry:
        reg_list = registry['files']

    all_problems = []
    registry_paths = {e.get('path', '') for e in reg_list}

    # 1. Hardcoded imports (critical — breaks on next rename)
    all_problems.extend(_scan_hardcoded_pigeon_imports(root, registry_paths))

    # 2. Dead exports (unused public functions)
    all_problems.extend(_scan_dead_exports(root, reg_list))

    # 3. Duplicate docstrings
    all_problems.extend(_scan_duplicate_docstrings(root, reg_list))

    # 4. Cross-file coupling
    coupling_problems, import_graph = _scan_cross_file_coupling(root, reg_list)
    all_problems.extend(coupling_problems)

    # 5. Query memory noise
    all_problems.extend(_scan_query_noise(root))

    # Sort by severity
    sev_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3, 'info': 4}
    all_problems.sort(key=lambda p: sev_order.get(p.get('severity', 'info'), 5))

    # Build cross-file context for changed files
    cross_context = {}
    if changed_py:
        for rel in changed_py:
            deps = import_graph.get(rel, set())
            dependents = [f for f, d in import_graph.items() if rel in d]
            if deps or dependents:
                cross_context[rel] = {
                    'imports_from': sorted(deps),
                    'imported_by': sorted(dependents),
                }

    return {
        'problems': all_problems,
        'cross_context': cross_context,
        'total_files_scanned': len(reg_list),
        'import_graph_size': len(import_graph),
    }


def write_self_fix_report(root: Path, report: dict, commit_hash: str = '') -> Path:
    """Write problem report to docs/self_fix/."""
    from datetime import datetime, timezone
    out_dir = root / 'docs' / 'self_fix'
    out_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    tag = f'_{commit_hash}' if commit_hash else ''
    out_path = out_dir / f'{today}{tag}_self_fix.md'

    lines = [
        f'# Self-Fix Report — {today} {commit_hash}',
        f'',
        f'Scanned {report["total_files_scanned"]} modules, '
        f'{report["import_graph_size"]} in import graph.',
        f'',
    ]

    problems = report['problems']
    if problems:
        lines.append(f'## Problems Found: {len(problems)}')
        lines.append('')
        for i, p in enumerate(problems, 1):
            sev = p.get('severity', '?').upper()
            lines.append(f'### {i}. [{sev}] {p["type"]}')
            if 'file' in p:
                lines.append(f'- **File**: {p["file"]}')
            if 'line' in p:
                lines.append(f'- **Line**: {p["line"]}')
            if 'function' in p:
                lines.append(f'- **Function**: `{p["function"]}()`')
            if 'import' in p:
                lines.append(f'- **Import**: `{p["import"]}`')
            if 'count' in p:
                lines.append(f'- **Count**: {p["count"]}')
            if 'fan_in' in p:
                lines.append(f'- **Fan-in**: {p["fan_in"]} dependents')
            lines.append(f'- **Fix**: {p["fix"]}')
            lines.append('')
    else:
        lines.append('## No problems found.')
        lines.append('')

    cross = report.get('cross_context', {})
    if cross:
        lines.append('## Cross-File Context (changed files)')
        lines.append('')
        for rel, ctx in cross.items():
            lines.append(f'### {rel}')
            if ctx['imports_from']:
                lines.append(f'- **Imports from**: {", ".join(ctx["imports_from"])}')
            if ctx['imported_by']:
                lines.append(f'- **Imported by**: {", ".join(ctx["imported_by"])}')
            lines.append('')

    out_path.write_text('\n'.join(lines), encoding='utf-8')
    return out_path
