"""planner_seq002_v001.py — Generate rename plan for non-compliant files.

Takes scanner output, assigns sequence numbers per folder,
produces old_path → new_path map with module path translations.
Includes description + intent slugs in filenames via nametag.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v004 | 109 lines | ~919 tokens
# DESC:   generate_rename_plan_for_non
# INTENT: verify_pigeon_plugin
# LAST:   2026-03-15 @ caac48c
# SESSIONS: 1
# ──────────────────────────────────────────────
import re
from datetime import datetime, timezone
from pathlib import Path

from pigeon_compiler.rename_engine.nametag_seq011_v003_d0314__encode_file_description_intent_into_lc_desc_upgrade import (
    extract_desc_slug,
    build_nametag,
    build_glyph_prefix,
    build_nametag_with_glyphs,
)

SEQ_PATTERN = re.compile(r'_seq(\d{3})_v(\d{3})\.py$')


def _load_glyph_data(root: Path) -> tuple[dict, dict, dict]:
    """Load glyph map + confidence map + partners for filename encoding."""
    glyph_map: dict[str, str] = {}
    confidence_map: dict[str, str] = {}
    partners: dict[str, list[dict]] = {}
    if root is None:
        return glyph_map, confidence_map, partners
    try:
        from src.symbol_dictionary_seq031_v002_d0401__典双逆流_symbol_dictionary_generator_for_pigeon_lc_glyph_compiler_symbol import (
            _MNEMONIC_MAP,
        )
        glyph_map = dict(_MNEMONIC_MAP)
    except Exception:
        pass
    try:
        from src.confidence_scorer_seq033_v001 import score_module_confidence
        confidence_map = score_module_confidence(root)
    except Exception:
        pass
    try:
        import json
        fp = root / 'file_profiles.json'
        if fp.exists():
            profiles = json.loads(fp.read_text('utf-8'))
            for mod, data in profiles.items():
                p = data.get('partners', [])
                if p:
                    partners[mod] = p
    except Exception:
        pass
    return glyph_map, confidence_map, partners


def build_rename_plan(catalog: dict, version: str = '001',
                     root: Path = None,
                     intent: str = 'initial_naming') -> dict:
    """Build a complete rename plan from scanner catalog.

    Groups files by folder, assigns sequence numbers,
    preserves already-compliant files' sequence numbers.
    Returns plan with 'renames' list and 'import_map'.
    intent = what action triggered this rename cycle.
    """
    files = catalog['files']
    by_folder = _group_by_folder(files)
    renames = []
    import_map = {}
    today = datetime.now(timezone.utc).strftime('%m%d')
    glyph_map, confidence_map, partners = _load_glyph_data(root)

    for folder, folder_files in sorted(by_folder.items()):
        used_seqs = _collect_existing_seqs(folder_files)
        next_seq = max(used_seqs, default=0) + 1

        for f in folder_files:
            if f['is_pigeon'] or f['is_init']:
                continue
            base_name = _make_pigeon_stem(f['stem'], next_seq, version, today)
            py_path = Path(root) / f['path'] if root else None
            desc_slug = ''
            if py_path and py_path.exists():
                desc_slug = extract_desc_slug(py_path)
            # Build glyph prefix if data available
            mod_root = re.sub(r'_seq\d{3}.*$', '', f['stem']).lstrip('.')
            glyph_prefix = ''
            if glyph_map and py_path and py_path.exists():
                glyph_prefix = build_glyph_prefix(
                    py_path, mod_root, glyph_map, confidence_map,
                    partners=partners,
                )
            if glyph_prefix:
                new_name = build_nametag_with_glyphs(
                    base_name, desc_slug, intent, glyph_prefix,
                )
            else:
                new_name = build_nametag(base_name, desc_slug, intent)
            new_path = f"{folder}/{new_name}" if folder else new_name
            old_module = f['module_path']
            new_module = new_path.replace('/', '.').removesuffix('.py')
            renames.append({
                'old_path': f['path'],
                'new_path': new_path,
                'old_module': old_module,
                'new_module': new_module,
                'folder': folder,
                'old_stem': f['stem'],
                'new_stem': new_name.removesuffix('.py'),
            })
            import_map[old_module] = new_module
            next_seq += 1

    return {
        'renames': renames,
        'import_map': import_map,
        'stats': {
            'total_renames': len(renames),
            'folders_affected': len(set(r['folder'] for r in renames)),
        }
    }


def _group_by_folder(files: list) -> dict:
    groups = {}
    for f in files:
        folder = f['folder']
        groups.setdefault(folder, []).append(f)
    return groups


def _collect_existing_seqs(files: list) -> list:
    seqs = []
    for f in files:
        m = SEQ_PATTERN.search(f['path'])
        if m:
            seqs.append(int(m.group(1)))
    return seqs


def _make_pigeon_stem(stem: str, seq: int, version: str,
                      date: str = '') -> str:
    """Convert a plain stem to Pigeon Code base stem (no extension).

    routes → routes_seq001_v001_d0615
    email_sender → email_sender_seq002_v001_d0615
    """
    clean = re.sub(r'_seq\d{3}_v\d{3}(_d\d{4})?(__[a-z0-9_]+)?$', '', stem)
    base = f"{clean}_seq{seq:03d}_v{version}"
    if date:
        base += f"_d{date}"
    return base
