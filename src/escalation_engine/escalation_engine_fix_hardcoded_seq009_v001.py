"""escalation_engine_fix_hardcoded_seq009_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v001 | 18 lines | ~241 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path

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
