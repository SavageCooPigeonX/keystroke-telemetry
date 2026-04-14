"""escalation_engine_fix_over_cap_seq011_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 011 | VER: v001 | 32 lines | ~371 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path

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
