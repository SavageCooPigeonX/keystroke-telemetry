"""One-shot self-fix analyzer: cross-file problem detection + targeted resolution."""

# ── pigeon ────────────────────────────────────
# SEQ: 013 | VER: v011 | 632 lines | ~5,846 tokens
# DESC:   one_shot_self_fix_analyzer
# INTENT: dynamic_import_resolvers
# LAST:   2026-03-28 @ b1971c0
# SESSIONS: 8
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   2026-03-22T01:45:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  fix registry files key + skip compiled subdir
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
    """Find pigeon-tracked files that exceed the 200-line hard cap.

    Skips files matched by pigeon_limits.is_excluded() — compiler orchestrators,
    prompt templates, intentional monoliths, vscode-extension entry points, client
    scripts, and test harnesses are never auto-compiled.
    """
    problems = []
    try:
        from pigeon_compiler.pigeon_limits import PIGEON_MAX, is_excluded
    except ImportError:
        PIGEON_MAX = 200
        is_excluded = lambda p, root=None: False  # noqa: E731
    if isinstance(registry, list):
        reg_list = registry
    elif isinstance(registry, dict) and 'files' in registry:
        reg_list = registry['files']
    else:
        reg_list = list(registry.values())
    for entry in reg_list:
        if not isinstance(entry, dict):
            continue
        rel = entry.get('path', '')
        if not rel.endswith('.py'):
            continue
        abs_p = root / rel
        if not abs_p.exists():
            continue
        # Skip anything that should never be auto-compiled
        if is_excluded(abs_p):
            continue
        # Skip if a compiled subdir already exists (seq base dir with __init__.py)
        import re as _re
        _seq_m = _re.match(r'([\w]+_seq\d+)', abs_p.stem)
        if _seq_m:
            _compiled = abs_p.parent / _seq_m.group(1)
            if (_compiled / '__init__.py').exists():
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

    # Skip files that already have a compiled package directory alongside them
    # (stem without version suffix → look for a matching subdir in same parent)
    import re as _re2
    def _already_compiled(rel: str) -> bool:
        abs_p = root / rel
        m = _re2.match(r'([\w]+_seq\d+)', abs_p.stem)
        if not m:
            return False
        pkg_stem = m.group(1)
        return (abs_p.parent / pkg_stem).is_dir()

    over_cap = [p for p in over_cap if not _already_compiled(p['file'])]
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
        from pigeon_compiler.runners.run_clean_split_seq010_v006_d0322__full_clean_pipeline_deepseek_plan_lc_windows_max_path import run as _run_split
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

# Pattern: `from src.logger_seq003_v003_d0317__... import TelemetryLogger` (indented OK)
_HC_FROM_IMPORT = re.compile(
    r'^([ \t]*)(from\s+src\.([\.\w]+_seq\d+_v\d+_d\d+__[\w]+)\s+import\s+([\w,][^\n]*))',
    re.MULTILINE,
)
# Pattern: `import src.logger_seq003_v003_d0317__...`
_HC_BARE_IMPORT = re.compile(
    r'^([ \t]*)(import\s+src\.([\w]+_seq\d+_v\d+_d\d+__[\w]+))',
    re.MULTILINE,
)


def _seq_base(full_name: str) -> str:
    """Extract `logger_seq003` from `logger_seq003_v003_d0317__core_logger`.
    
    Also handles dotted paths: `cognitive.adapter_seq001_v002_...`
    → `cognitive.adapter_seq001`.
    """
    # Split on dots and find the seq part in the last segment
    parts = full_name.rsplit('.', 1)
    last = parts[-1] if len(parts) > 1 else full_name
    prefix = (parts[0] + '.') if len(parts) > 1 else ''
    m = re.match(r'([\w]+_seq\d+)', last)
    if m:
        return prefix + m.group(1)
    return prefix + last.split('_')[0] + '_seq'


def auto_apply_import_fixes(root: Path, dry_run: bool = False) -> list[dict]:
    """Scan hardcoded pigeon imports and rewrite to use _resolve.py pattern.

    Rewrites `from src.module_seq003_v003_... import Foo, Bar` to:
        from src._resolve import src_import
        Foo, Bar = src_import("module_seq003", "Foo", "Bar")

    This is safe because src_import() resolves at runtime via glob,
    surviving any pigeon rename. No more naive str.replace corruption.
    """
    root = Path(root)
    results = []

    for py in sorted(root.rglob('*.py')):
        rel_parts = py.relative_to(root).parts
        if any(p in {'.venv', '__pycache__', '.git', 'node_modules'} for p in rel_parts):
            continue
        # Skip the resolver itself
        if py.name == '_resolve.py':
            continue

        try:
            text = py.read_text(encoding='utf-8')
        except Exception:
            continue

        if '_seq' not in text or '_v' not in text:
            continue

        lines = text.splitlines(keepends=True)
        new_lines = []
        changed = False
        needs_resolve_import = False

        for line in lines:
            # Check from-import pattern
            m = _HC_FROM_IMPORT.match(line)
            if m:
                indent = m.group(1)
                mod_full = m.group(3)
                symbols_raw = m.group(4)
                symbols = [s.strip().rstrip(')') for s in symbols_raw.split(',') if s.strip()]
                # Skip parenthesized multi-line imports (just flag them)
                if '(' in symbols_raw and ')' not in symbols_raw:
                    new_lines.append(line)
                    continue
                symbols = [s for s in symbols if s and s != '(']
                base = _seq_base(mod_full)
                if len(symbols) == 1:
                    new_line = f'{indent}{symbols[0]} = src_import("{base}", "{symbols[0]}")\n'
                else:
                    lhs = ', '.join(symbols)
                    args = ', '.join(f'"{s}"' for s in symbols)
                    new_line = f'{indent}{lhs} = src_import("{base}", {args})\n'
                new_lines.append(new_line)
                needs_resolve_import = True
                changed = True
                results.append({'file': str(py.relative_to(root)),
                                'old_import': line.strip(),
                                'new_expr': new_line.strip(),
                                'applied': not dry_run})
                continue

            # Check bare-import pattern
            m2 = _HC_BARE_IMPORT.match(line)
            if m2:
                indent = m2.group(1)
                mod_full = m2.group(3)
                base = _seq_base(mod_full)
                alias = base.split('_seq')[0]
                new_line = f'{indent}{alias} = src_import("{base}")\n'
                new_lines.append(new_line)
                needs_resolve_import = True
                changed = True
                results.append({'file': str(py.relative_to(root)),
                                'old_import': line.strip(),
                                'new_expr': new_line.strip(),
                                'applied': not dry_run})
                continue

            new_lines.append(line)

        if not changed or dry_run:
            continue

        # Inject `from src._resolve import src_import` if not present
        new_text = ''.join(new_lines)
        if needs_resolve_import and 'from src._resolve import src_import' not in new_text:
            # Remove any old _load_src helper if present
            new_text = re.sub(
                r'\ndef _load_src\(pattern:.*?return tuple\(.*?\)\n',
                '\n', new_text, flags=re.DOTALL)
            # Insert resolve import after pigeon header or first import
            insert_lines = new_text.splitlines(keepends=True)
            insert_pos = 0
            for i, ln in enumerate(insert_lines[:30]):
                if ln.strip().startswith(('import ', 'from ')):
                    insert_pos = i
            insert_lines.insert(insert_pos + 1,
                                'from src._resolve import src_import\n')
            new_text = ''.join(insert_lines)

        py.write_text(new_text, encoding='utf-8')

    return results
