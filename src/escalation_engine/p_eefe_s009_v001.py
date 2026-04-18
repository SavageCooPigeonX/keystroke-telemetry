"""escalation_engine_seq001_v001_fix_executors_seq009_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v001 | 89 lines | ~992 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json, shutil, subprocess, importlib.util

def _fix_hardcoded_imports(root: Path, module: str, registry_entry: dict) -> dict:
    """Fix hardcoded pigeon imports via auto_apply_import_fixes."""
    try:
        sf_mod = _load_glob_module(root, 'src/修_sf_s013', '修f_sf_aaif*')
        if sf_mod and hasattr(sf_mod, 'auto_apply_import_fixes'):
            results = sf_mod.auto_apply_import_fixes(root, dry_run=False)
            applied = [r for r in results if r.get('applied')]
            return {
                'success': len(applied) > 0,
                'description': f'rewrote {len(applied)} hardcoded import(s)',
                'details': applied[:5],
            }
    except Exception as e:
        return {'success': False, 'description': f'import fix failed: {e}', 'details': []}
    return {'success': False, 'description': 'auto_apply_import_fixes not found', 'details': []}


def _fix_dead_exports(root: Path, module: str, registry_entry: dict) -> dict:
    """Remove dead exports from a module file."""
    fpath = root / registry_entry.get('path', '')
    if not fpath.exists():
        return {'success': False, 'description': f'file not found: {fpath}', 'details': []}

    try:
        import ast
        source = fpath.read_text(encoding='utf-8')
        tree = ast.parse(source)

        # find functions that are exported but never imported elsewhere
        sf_mod = _load_glob_module(root, 'src', '修f_sf*')
        if not sf_mod:
            return {'success': False, 'description': 'self-fix scanner not found', 'details': []}

        # use the dead export scanner to identify targets
        reg_data = json.loads((root / 'pigeon_registry.json').read_text(encoding='utf-8'))
        registry = reg_data if isinstance(reg_data, dict) else {'files': reg_data}

        # for safety — only mark removal, don't delete yet
        # dead export removal is complex (might break dynamic imports)
        return {
            'success': False,
            'description': 'dead export removal deferred — requires operator confirmation',
            'details': [{'module': module, 'reason': 'dynamic import risk'}],
        }
    except Exception as e:
        return {'success': False, 'description': f'dead export analysis failed: {e}', 'details': []}


def _fix_over_hard_cap(root: Path, module: str, registry_entry: dict) -> dict:
    """Split an oversized file via pigeon compiler."""
    fpath = root / registry_entry.get('path', '')
    if not fpath.exists():
        return {'success': False, 'description': f'file not found: {fpath}', 'details': []}

    tokens = registry_entry.get('tokens', 0)
    if tokens < 2000:
        return {'success': False, 'description': f'tokens={tokens} < 2000, not over cap', 'details': []}

    try:
        split_mod = _load_glob_module(root, 'pigeon_compiler/runners', '净拆f_rcs*')
        if split_mod and hasattr(split_mod, 'run'):
            # get dead exports to exclude from splits
            dead_exports = []
            dossier_entry = registry_entry.get('bug_keys', [])
            if 'de' in dossier_entry:
                # could load from self-fix scan, but keep it simple
                pass

            split_mod.run(fpath, exclude_symbols=dead_exports)
            return {
                'success': True,
                'description': f'split {module} ({tokens} tokens)',
                'details': [{'file': str(fpath), 'tokens': tokens}],
            }
    except Exception as e:
        return {'success': False, 'description': f'split failed: {e}', 'details': []}
    return {'success': False, 'description': 'pigeon split runner not found', 'details': []}


FIX_DISPATCH = {
    'hardcoded_import': _fix_hardcoded_imports,
    'dead_export': _fix_dead_exports,
    'over_hard_cap': _fix_over_hard_cap,
    'duplicate_docstring': _fix_duplicate_docstring,
}
