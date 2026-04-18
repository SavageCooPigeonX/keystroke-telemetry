"""escalation_engine_seq001_v001_fix_dead_exports_seq010_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 010 | VER: v001 | 33 lines | ~387 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json, shutil, subprocess, importlib.util

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
