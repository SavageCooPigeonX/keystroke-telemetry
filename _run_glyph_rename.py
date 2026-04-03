"""Standalone glyph rename — adds Chinese character prefixes to pigeon-compliant files.

ONLY touches files that already have pigeon naming (seq/ver/date).
Does NOT rename non-compliant files. Does NOT change desc/intent slugs.
Just adds/updates the Chinese glyph prefix in the description slug.

Usage:
  py _run_glyph_rename.py          # dry run
  py _run_glyph_rename.py --execute # live rename
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()

# ── Load glyph map ──────────────────────────
def _load_glyph_map():
    try:
        from src.典w_sd_s031_v002_d0401_缩分话_λG import (
            _MNEMONIC_MAP,
        )
        return dict(_MNEMONIC_MAP)
    except Exception as e:
        print(f'[ERROR] Cannot load glyph map: {e}')
        sys.exit(1)


def _load_partners():
    fp = ROOT / 'file_profiles.json'
    partners = {}
    if fp.exists():
        try:
            profiles = json.loads(fp.read_text('utf-8'))
            for mod, data in profiles.items():
                p = data.get('partners', [])
                if p:
                    partners[mod] = p
        except Exception:
            pass
    return partners


# ── Nametag parsing ─────────────────────────
_NAMETAG_RE = re.compile(
    r'^(?P<base>.+_seq\d{3}_v\d{3}(?:_d\d{4})?)(?:__(?P<slug>.+))?\.py$'
)
_GLYPH_PREFIX_RE = re.compile(r'^([\u4e00-\u9fff]+)(?:_|$)')
_LC_SEP = '_lc_'


def _parse(name):
    m = _NAMETAG_RE.match(name)
    if not m:
        return None
    base = m.group('base')
    slug = m.group('slug') or ''
    desc = slug
    intent = ''
    if _LC_SEP in slug:
        desc, intent = slug.split(_LC_SEP, 1)
    glyph_prefix = ''
    gm = _GLYPH_PREFIX_RE.match(desc)
    if gm:
        glyph_prefix = gm.group(1)
    return {
        'base': base,
        'desc': desc,
        'intent': intent,
        'glyph_prefix': glyph_prefix,
    }


def _extract_module_root(stem):
    """self_fix_seq013_v011_d0328__... → self_fix"""
    return re.sub(r'_seq\d{3}.*$', '', stem).lstrip('.')


def _extract_internal_imports(py_path):
    """Get imported module root names from a .py file."""
    mods = []
    try:
        text = py_path.read_text('utf-8', errors='ignore')
    except Exception:
        return mods
    for line in text.splitlines():
        line = line.strip()
        if line.startswith(('import ', 'from ')):
            # Extract the module path
            if line.startswith('from '):
                parts = line.split()
                if len(parts) >= 2:
                    mod = parts[1]
                else:
                    continue
            else:
                parts = line.split()
                if len(parts) >= 2:
                    mod = parts[1]
                else:
                    continue
            # Only internal modules (src., pigeon_compiler., etc.)
            if mod.startswith(('src.', 'pigeon_compiler.', 'pigeon_brain.', 'streaming_layer.', 'client.')):
                # Extract the root module name from the leaf
                leaf = mod.rsplit('.', 1)[-1]
                root_name = re.sub(r'_seq\d{3}.*$', '', leaf).lstrip('.')
                if root_name:
                    mods.append(root_name)
    return mods


def _build_glyph_prefix(py_path, module_name, glyph_map, partners, max_deps=3):
    """Build Chinese-only glyph prefix: own_char + dep_chars."""
    own = glyph_map.get(module_name, '')
    if not own:
        return ''

    deps = []
    if partners and module_name in partners:
        for p in partners[module_name]:
            g = glyph_map.get(p.get('name', ''), '')
            if g and g != own and g not in deps:
                deps.append(g)
            if len(deps) >= max_deps:
                break

    if not deps and py_path.exists():
        for imp in _extract_internal_imports(py_path):
            if imp == module_name:
                continue
            g = glyph_map.get(imp, '')
            if g and g != own and g not in deps:
                deps.append(g)
            if len(deps) >= max_deps:
                break

    return own + ''.join(deps)


def _build_new_name(parsed, glyph_prefix):
    """Build new filename with glyph prefix in desc slug."""
    desc = parsed['desc']
    # Strip old glyph prefix
    old_gp = parsed['glyph_prefix']
    if old_gp and desc.startswith(old_gp):
        desc = desc[len(old_gp):].lstrip('_')

    if glyph_prefix and desc:
        new_desc = f'{glyph_prefix}_{desc}'
    elif glyph_prefix:
        new_desc = glyph_prefix
    else:
        new_desc = desc

    slug = new_desc
    if parsed['intent']:
        slug = f'{new_desc}{_LC_SEP}{parsed["intent"]}'

    if slug:
        return f'{parsed["base"]}__{slug}.py'
    return f'{parsed["base"]}.py'


# ── Scan ────────────────────────────────────
SKIP_DIRS = {'.git', '__pycache__', 'node_modules', '.venv', 'venv',
             'pigeon_code.egg-info', '.mypy_cache', 'build', 'dist',
             'vscode-extension', 'chrome-extension', 'demo_logs', 'test_logs',
             'stress_logs', 'logs', 'docs'}

MAX_PATH = 259


def scan_glyph_renames(glyph_map, partners):
    """Find all pigeon files that need glyph prefix updates."""
    renames = []
    for py in sorted(ROOT.rglob('*.py')):
        rel = py.relative_to(ROOT)
        # Skip excluded dirs
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        # Only pigeon-compliant files (have seq pattern)
        parsed = _parse(py.name)
        if not parsed:
            continue

        mod_root = _extract_module_root(py.stem)
        expected_prefix = _build_glyph_prefix(py, mod_root, glyph_map, partners)

        if not expected_prefix:
            continue  # module not in glyph map

        if parsed['glyph_prefix'] == expected_prefix:
            continue  # already has correct prefix

        new_name = _build_new_name(parsed, expected_prefix)
        new_path = py.parent / new_name

        # MAX_PATH guard
        if len(str(new_path)) > MAX_PATH:
            print(f'  [SKIP] path too long ({len(str(new_path))} chars): {rel}')
            continue

        # Validate new module name is valid Python
        new_stem = new_name.removesuffix('.py')
        if not new_stem.isidentifier():
            print(f'  [SKIP] invalid identifier: {new_stem}')
            continue

        renames.append({
            'old_path': str(rel).replace('\\', '/'),
            'new_path': str(new_path.relative_to(ROOT)).replace('\\', '/'),
            'old_name': py.name,
            'new_name': new_name,
            'module_root': mod_root,
            'old_prefix': parsed['glyph_prefix'],
            'new_prefix': expected_prefix,
        })

    return renames


# ── Execute ─────────────────────────────────
def execute_renames(renames, dry_run=True):
    """Rename files and rewrite imports."""
    if not renames:
        print('No glyph renames needed.')
        return

    print(f'\n{"DRY RUN" if dry_run else "EXECUTING"}: {len(renames)} glyph renames\n')

    # Show first 20
    for r in renames[:20]:
        print(f'  {r["old_prefix"] or "(none)":>6} → {r["new_prefix"]:>6}  {r["old_name"]}')
    if len(renames) > 20:
        print(f'  ... and {len(renames) - 20} more')

    if dry_run:
        print(f'\nDRY RUN — {len(renames)} files would be renamed. Use --execute to apply.')
        return

    # Build import map
    import_map = {}
    for r in renames:
        old_mod = r['old_path'].replace('/', '.').removesuffix('.py')
        new_mod = r['new_path'].replace('/', '.').removesuffix('.py')
        import_map[old_mod] = new_mod

    # Step 1: Rewrite imports FIRST (before files move)
    print(f'\n[1/3] Rewriting imports ({len(import_map)} mappings)...')
    from pigeon_compiler.rename_engine.引w_ir_s003_v005_d0403_踪稿析_λFX import rewrite_all_imports
    changes = rewrite_all_imports(ROOT, import_map, dry_run=False)
    print(f'      Rewrote {len(changes)} import lines')

    # Step 2: Rename files
    print(f'[2/3] Renaming {len(renames)} files...')
    renamed = []
    errors = []
    rollback = []
    for i, r in enumerate(renames, 1):
        old = ROOT / r['old_path']
        new = ROOT / r['new_path']
        try:
            if not old.exists():
                errors.append(f'missing: {r["old_path"]}')
                continue
            new.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old), str(new))
            renamed.append(r['new_path'])
            rollback.append(r)
            if i % 50 == 0:
                print(f'      ... {i}/{len(renames)}')
        except Exception as e:
            errors.append(f'{r["old_path"]}: {e}')

    print(f'      Renamed {len(renamed)} files, {len(errors)} errors')

    # Step 3: Validate imports
    print(f'[3/3] Validating imports...')
    from pigeon_compiler.rename_engine.审p_va_s005_v005_d0403_踪稿析_λFX import validate_imports
    val = validate_imports(ROOT)
    if val['valid']:
        print(f'      PASS — all imports valid')
    else:
        broken = val.get('broken', [])
        print(f'      WARNING: {len(broken)} broken imports')
        for b in broken[:10]:
            print(f'        {b}')

    if errors:
        print(f'\nErrors:')
        for e in errors[:10]:
            print(f'  {e}')

    # Save rollback
    if rollback:
        rb_path = ROOT / 'logs' / 'glyph_rename_rollback.json'
        rb_path.parent.mkdir(exist_ok=True)
        rb_path.write_text(json.dumps({
            'renames': [{'old': r['old_path'], 'new': r['new_path']} for r in rollback]
        }, indent=2), encoding='utf-8')
        print(f'\nRollback saved: {rb_path.relative_to(ROOT)}')


def main():
    execute = '--execute' in sys.argv

    print('=== PIGEON GLYPH RENAME ===')
    print('Loading glyph map...')
    glyph_map = _load_glyph_map()
    print(f'  {len(glyph_map)} glyphs loaded')

    print('Loading partner data...')
    partners = _load_partners()
    print(f'  {len(partners)} modules with partner data')

    print('Scanning for glyph drift...')
    renames = scan_glyph_renames(glyph_map, partners)

    execute_renames(renames, dry_run=not execute)


if __name__ == '__main__':
    main()
