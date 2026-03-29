"""self_fix_seq013_scan_over_hard_cap_decomposed_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

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
