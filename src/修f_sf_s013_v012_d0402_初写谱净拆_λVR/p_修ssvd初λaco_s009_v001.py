"""修f_sf_s013_v012_d0402_初写谱净拆_λVR_auto_compile_oversized_seq009_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

def auto_compile_oversized(
    root: Path,
    fix_report: dict,
    max_files: int = 5,
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
        from pigeon_compiler.runners.净拆f_rcs_s010_v006_d0322_译测编深划_λW import run as _run_split
    except ImportError:
        # glob-safe fallback import
        import importlib.util
        matches = sorted((root / 'pigeon_compiler' / 'runners').glob('净拆f_rcs_s010*.py'))
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
