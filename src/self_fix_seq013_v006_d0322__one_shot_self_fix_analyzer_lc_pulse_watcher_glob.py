"""One-shot self-fix analyzer: cross-file problem detection + targeted resolution."""

# ── pigeon ────────────────────────────────────
# SEQ: 013 | VER: v006 | 572 lines | ~5,213 tokens
# DESC:   one_shot_self_fix_analyzer
# INTENT: pulse_watcher_glob
# LAST:   2026-03-22 @ d447b19
# SESSIONS: 3
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   2026-03-22T00:30:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  short target_name fix Windows MAX_PATH
# EDIT_STATE: harvested
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


def _scan_over_hard_cap(root: Path, registry: dict) -> list[dict]:
    """Find pigeon-tracked files that exceed the 200-line hard cap."""
    problems = []
    from pigeon_compiler.pigeon_limits import PIGEON_MAX
    reg_list = registry if isinstance(registry, list) else list(registry.values())
    for entry in reg_list:
        if not isinstance(entry, dict):
            continue
        rel = entry.get('path', '')
        if not rel.endswith('.py'):
            continue
        abs_p = root / rel
        if not abs_p.exists():
            continue
        try:
            lc = len(abs_p.read_text(encoding='utf-8').splitlines())
        except Exception:
            continue
        if lc > PIGEON_MAX:
            problems.append({
                'type': 'over_hard_cap',
                'file': rel,
                'line_count': lc,
                'severity': 'high',
                'fix': f'Auto-compile with pigeon compiler (run_clean_split)',
            })
    return problems


def auto_compile_oversized(
    root: Path,
    fix_report: dict,
    max_files: int = 2,
) -> list[dict]:
    """Auto-compile files flagged over_hard_cap, pruning confirmed dead exports.

    Called from git_plugin after run_self_fix. Invokes run_clean_split on each
    oversized file, passing dead exports as exclusions to the DeepSeek prompt
    so they are pruned from the split output — never survive a compile cycle.

    Returns list of dicts: {file, status, output_dir, error}.
    """
    import sys
    sys.path.insert(0, str(root))

    problems = fix_report.get('problems', [])
    over_cap = [
        p for p in problems
        if p.get('type') == 'over_hard_cap'
    ][:max_files]

    if not over_cap:
        return []

    # Build per-file dead export index
    dead_by_file: dict[str, list[str]] = {}
    for p in problems:
        if p.get('type') == 'dead_export':
            f = p.get('file', '')
            fn = p.get('function', '')
            if f and fn:
                dead_by_file.setdefault(f, []).append(fn)

    results = []
    try:
        from pigeon_compiler.runners.run_clean_split_seq010_v005_d0322__full_clean_pipeline_deepseek_plan_lc_auto_compile_oversized import run as _run_split
    except ImportError:
        # glob-safe fallback import
        import importlib.util
        matches = sorted((root / 'pigeon_compiler' / 'runners').glob('run_clean_split_seq010*.py'))
        if not matches:
            return [{'file': '?', 'status': 'error', 'error': 'run_clean_split not found'}]
        spec = importlib.util.spec_from_file_location('run_clean_split', matches[-1])
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _run_split = mod.run

    for p in over_cap:
        rel = p['file']
        abs_p = root / rel
        dead = dead_by_file.get(rel, [])
        # Use short seq-base as target name to avoid Windows MAX_PATH (260 chars)
        import re as _re
        m = _re.match(r'([\w]+_seq\d+)', abs_p.stem)
        short_name = m.group(1) if m else abs_p.stem[:40]
        try:
            result = _run_split(abs_p, target_name=short_name, exclude_symbols=dead)
            results.append({
                'file': rel,
                'status': 'ok',
                'output_dir': result.get('target', ''),
                'files': result.get('files', 0),
                'dead_pruned': dead,
            })
        except Exception as e:
            results.append({'file': rel, 'status': 'error', 'error': str(e)})

    return results


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

    # 6. Over-hard-cap files (need auto-compile)
    all_problems.extend(_scan_over_hard_cap(root, reg_list))

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


# ── Auto-apply fix for CRITICAL hardcoded imports ─────────────────────────────

_LOAD_SRC_HELPER = '''
def _load_src(pattern: str, *symbols):
    """Dynamic pigeon import — finds latest src/ file matching glob."""
    import importlib.util as _ilu, glob as _g
    matches = sorted(_g.glob(f'src/{pattern}'))
    if not matches:
        raise ImportError(f'No src/ file matches {pattern!r}')
    spec = _ilu.spec_from_file_location('_dyn', matches[-1])
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if len(symbols) == 1:
        return getattr(mod, symbols[0])
    return tuple(getattr(mod, s) for s in symbols)

'''.lstrip('\n')

# Pattern: `from src.logger_seq003_v003_d0317__... import TelemetryLogger` (indented OK)
_HC_FROM_IMPORT = re.compile(
    r'^([ \t]*from\s+src\.([\.\w]+_seq\d+_v\d+_d\d+__[\w]+)\s+import\s+([\w,][^\n]*))',
    re.MULTILINE,
)
# Pattern: `import src.logger_seq003_v003_d0317__...`
_HC_BARE_IMPORT = re.compile(
    r'^(import\s+src\.([\w]+_seq\d+_v\d+_d\d+__[\w]+))',
    re.MULTILINE,
)


def _seq_base(full_name: str) -> str:
    """Extract `logger_seq003` from `logger_seq003_v003_d0317__core_logger`."""
    m = re.match(r'([\w]+_seq\d+)', full_name)
    return m.group(1) if m else full_name.split('_')[0] + '_seq'


def auto_apply_import_fixes(root: Path, dry_run: bool = False) -> list[dict]:
    """Scan for CRITICAL hardcoded pigeon imports and rewrite them in-place.

    For each `from src.module_seq003_v003_... import Foo, Bar` found:
      - Replaces the import line with `_load_src('module_seq003*.py', 'Foo', 'Bar')`
      - Injects `_load_src` helper function if not already present in the file.

    Returns list of {file, old_import, new_expr, applied: bool}.
    Skips pigeon_compiler/ internals and __init__.py (auto-managed elsewhere).
    Does NOT commit — caller is responsible for staging.
    """
    problems = _scan_hardcoded_pigeon_imports(root)
    if not problems:
        return []

    # Group by file
    by_file: dict[str, list[dict]] = {}
    for p in problems:
        by_file.setdefault(p['file'], []).append(p)

    results = []
    for rel, issues in by_file.items():
        filepath = root / rel.replace('/', os.sep)
        try:
            text = filepath.read_text(encoding='utf-8')
        except Exception:
            continue

        needs_helper = '_load_src' not in text
        changed = False
        replacements = []

        for m in _HC_FROM_IMPORT.finditer(text):
            full_line = m.group(1)
            mod_full = m.group(2)
            symbols_raw = m.group(3)
            symbols = [s.strip() for s in symbols_raw.split(',') if s.strip()]
            base = _seq_base(mod_full)
            glob_pat = f'{base}*.py'
            if len(symbols) == 1:
                new_expr = f'{symbols[0]} = _load_src({glob_pat!r}, {symbols[0]!r})'
            else:
                sym_list = ', '.join(f'{s!r}' for s in symbols)
                lhs = ', '.join(symbols)
                new_expr = f'{lhs} = _load_src({glob_pat!r}, {sym_list})'
            replacements.append((full_line, new_expr))
            results.append({'file': rel, 'old_import': full_line,
                            'new_expr': new_expr, 'applied': not dry_run})

        for m in _HC_BARE_IMPORT.finditer(text):
            full_line = m.group(1)
            mod_full = m.group(2)
            base = _seq_base(mod_full)
            glob_pat = f'{base}*.py'
            alias = base.split('_seq')[0]
            new_expr = f'{alias} = _load_src({glob_pat!r}, {alias!r})'
            replacements.append((full_line, new_expr))
            results.append({'file': rel, 'old_import': full_line,
                            'new_expr': new_expr, 'applied': not dry_run})

        if dry_run or not replacements:
            continue

        for old, new in replacements:
            text = text.replace(old, new, 1)
            changed = True

        if needs_helper and changed:
            # Inject helper after imports block (after last `import` line in first 30 lines)
            lines = text.splitlines(keepends=True)
            last_import_idx = 0
            for i, ln in enumerate(lines[:30]):
                if ln.strip().startswith(('import ', 'from ')):
                    last_import_idx = i
            insert_pos = last_import_idx + 1
            lines.insert(insert_pos, '\n' + _LOAD_SRC_HELPER)
            text = ''.join(lines)

        if changed:
            filepath.write_text(text, encoding='utf-8')

    return results
