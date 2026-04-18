"""虚f_mc_s036_v001_profile_find_module_path_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 27 lines | ~271 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def find_module_path(root: Path, module_name: str) -> str | None:
    reg = _jload(root / 'pigeon_registry.json')
    if reg:
        files = reg if isinstance(reg, list) else reg.get('files', [])
        for f in files:
            fname = f.get('file', '') or f.get('name', '')
            if module_name in fname:
                path = f.get('path', '')
                if path and (root / path).exists():
                    return path

    for search_dir in [root / 'src', root / 'pigeon_brain', root / 'pigeon_compiler']:
        if not search_dir.exists():
            continue
        for p in search_dir.rglob('*.py'):
            stem = p.stem
            if stem == module_name or stem.startswith(f'{module_name}_seq'):
                return str(p.relative_to(root))
        for p in search_dir.rglob('*.py'):
            stem = p.stem
            if module_name in stem:
                return str(p.relative_to(root))
    return None
