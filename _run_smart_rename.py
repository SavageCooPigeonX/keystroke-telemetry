"""Smart abbreviated rename — information-dense filenames.

Target format: {glyph}{state}_{abbrev}_s{seq}_v{ver}_d{date}_{dep_glyphs}_λ{intent}.py
Example:       修f_sf_s013_v011_d0328_叙算思_λM.py

For decomposed shards:
  Package dir:  思_cr_s014/
  Shard file:   思p_cr_ac_s007_v002_d0322_λ7.py

State codes: p=pass(✓) w=warn(~) f=fail(!) u=unknown(?)

Usage:
  py _run_smart_rename.py          # dry run
  py _run_smart_rename.py --execute # live rename
"""
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
MAX_PATH = 259

# ── Extra glyphs not in _MNEMONIC_MAP (auto-index assigns these algorithmically) ──
_EXTRA_GLYPHS = {
    'execution_logger': '读',
    'graph_extractor': '图',
    'graph_heat_map': '描',
    'loop_detector': '环检',
    'failure_detector': '缩',
    'observer_synthesis': '观',
    'dev_plan': '分',
    'node_awakener': '唤',
    'node_conversation': '话',
    'node_memory': '存',
    'predictor': '预',
    'prediction_scorer': '算',
    'learning_loop': '学',
    'fix_summary': '结',
    'flow_engine': '流',
    'path_selector': '择',
    'task_writer': '任',
    'vein_transport': '脉运',
    'func_decomposer': '译',
    'import_fixer': '踪',
    'class_decomposer': '织',
    'ether_map_builder': '拆',
    'intent_simulator': '意',
    'file_consciousness': '觉',
    'push_cycle': '环',
    'deepseek_plan_prompt': '核',
    'deepseek_adapter': '谱',
    'manifest_writer': '稿',
    'plan_parser': '析',
    'plan_validator': '验',
    'import_fixer': '踪',
    'source_slicer': '切',
    'call_graph': '演',
    'import_tracer': '追',
    'shared_state_detector': '共态',
    'ast_parser': '查',
}

# ── Manual abbreviation overrides for collision-prone names ──
_MANUAL_ABBREVS = {
    'cognitive_reactor': 'cr',
    'context_router': 'cxr',
    'context_budget': 'cb',
    'context_packet': 'cpk',
    '.operator_stats': 'ops',
    'operator_stats': 'ost',
    'compliance': 'cmp',
    'copilot_prompt_manager': 'cpm',
    'class_decomposer': 'cdp',
    'deepseek_adapter': 'dsa',
    'deepseek_plan_prompt': 'dspp',
    'demo_sim': 'dsm',
    'dev_plan': 'dvp',
    'drift_watcher': 'dw',
    'dual_substrate': 'dsb',
    'dynamic_prompt': 'dp',
    'prediction_scorer': 'ps',
    'press_release_gen_constants': 'prgc',
    'press_release_gen_template_builders': 'prgtb',
    'press_release_gen_template_helpers': 'prgth',
    'press_release_gen_template_key_findings': 'prgkf',
    'streaming_layer': 'sl',
    'streaming_layer_aggregator': 'sla',
    'streaming_layer_alerts': 'slal',
    'streaming_layer_connection_pool': 'slcp',
    'streaming_layer_constants': 'slc',
    'streaming_layer_dashboard': 'sld',
    'streaming_layer_dataclasses': 'sldc',
    'streaming_layer_demo_functions': 'sldf',
    'streaming_layer_demo_simulate': 'slds',
    'streaming_layer_demo_summary': 'sldy',
    'streaming_layer_formatter': 'slf',
    'streaming_layer_http_handler': 'slhh',
    'streaming_layer_metrics': 'slm',
    'streaming_layer_orchestrator': 'slo',
    'streaming_layer_replay': 'slr',
    'streaming_layer_simulation_helpers': 'slsh',
    'prompt_diff': 'pd',
    'prompt_enricher': 'pe',
    'prompt_journal': 'pj',
    'prompt_recon': 'prc',
    'prompt_signal': 'psg',
    'failure_detector': 'fdt',
    'func_decomposer': 'fdc',
    'manifest_writer': 'mw',
    'manifest_builder': 'mb',
    'manifest_bridge': 'mbr',
    'resistance_bridge': 'rb',
    'resistance_analyzer': 'ra',
    'rework_backfill': 'rwb',
    'rework_detector': 'rwd',
    'fix_summary': 'fxs',
    # operator_stats shards (non-standard naming — no parent seq in dir)
    'operator_stats_classify': 'oscl',
    'operator_stats_class': 'oscs',
    'operator_stats_compute': 'oscp',
    'operator_stats_constants': 'osct',
    'operator_stats_render_distribution': 'osrd',
    'operator_stats_render_full': 'osrf',
    'operator_stats_render_observations_decomposed': 'osro',
    'operator_stats_render_ranges': 'osrr',
    'operator_stats_render_recent': 'osrc',
    'operator_stats_render_tables': 'osrt',
    'operator_stats_render_timeframes_decomposed': 'ostd',
    'operator_stats_render_timeframes': 'ostf',
    'operator_stats_time_utils': 'ostu',
    # drift shards
    'drift_baseline_store': 'dbs',
    'drift_build_cognitive_context': 'dbcc',
    'drift_build_cognitive_context_helpers': 'dbch',
    'drift_compute_baseline': 'dcbl',
    'drift_detect_session_drift': 'ddsd',
}

# ── Stale / broken dirs to skip ──
_SKIP_DIR_NAMES = {
    '.operator_stats_seq008_v010_d0331__persi',  # truncated stale dir
}

# ── Data Loading ──────────────────────────────

def _load_glyph_map():
    try:
        from src.典w_sd_s031_v002_d0401_缩分话_λG import (
            _MNEMONIC_MAP, _INTENT_PREFIXES,
        )
        merged = dict(_MNEMONIC_MAP)
        merged.update(_EXTRA_GLYPHS)
        return merged, dict(_INTENT_PREFIXES)
    except Exception as e:
        print(f'[ERROR] Cannot load glyph/intent maps: {e}')
        sys.exit(1)


def _load_registry():
    reg = json.loads((ROOT / 'pigeon_registry.json').read_text('utf-8'))
    return reg.get('files', [])


def _load_profiles():
    fp = ROOT / 'file_profiles.json'
    if not fp.exists():
        return {}
    try:
        return json.loads(fp.read_text('utf-8'))
    except Exception:
        return {}


def _load_confidence():
    """Compute confidence states for all modules."""
    try:
        from src.u_cs_s033_v001 import score_module_confidence
        return score_module_confidence(ROOT)
    except Exception as e:
        print(f'[WARN] Cannot load confidence: {e}')
        return {}


# ── State Mapping ────────────────────────────

_STATE_MAP = {
    '✓': 'p',   # pass
    '~': 'w',   # warn
    '!': 'f',   # fail
    '?': 'u',   # unknown
}


def _state_char(confidence_scores, mod_name):
    sym = confidence_scores.get(mod_name, '?')
    return _STATE_MAP.get(sym, 'u')


# ── Abbreviation Engine ─────────────────────

def _abbreviate_word_list(words):
    """Generate abbreviation from word list."""
    if not words:
        return 'x'
    if len(words) == 1:
        w = words[0]
        return w[:2] if len(w) >= 2 else w
    return ''.join(w[0] for w in words if w)


def build_abbreviation_map(base_names):
    """Build collision-free abbreviation map for all base module names.

    Returns {base_name: abbreviation} like {'cognitive_reactor': 'cr', 'self_fix': 'sf'}
    """
    abbrevs = {}

    for name in sorted(base_names):
        # Use manual override if available
        if name in _MANUAL_ABBREVS:
            abbrevs[name] = _MANUAL_ABBREVS[name]
            continue
        clean = name.lstrip('.')
        words = [w for w in clean.split('_') if w]
        abbrevs[name] = _abbreviate_word_list(words)

    # ── Resolve collisions (up to 3 rounds) ──
    for _round in range(3):
        reverse = {}
        for name, abbr in abbrevs.items():
            reverse.setdefault(abbr, []).append(name)

        collisions = {a: ns for a, ns in reverse.items() if len(ns) > 1}
        if not collisions:
            break

        for abbr, names in collisions.items():
            for name in names:
                # Don't touch manual overrides
                if name in _MANUAL_ABBREVS:
                    continue
                clean = name.lstrip('.')
                words = [w for w in clean.split('_') if w]
                if len(words) == 1:
                    cur_len = len(abbrevs[name])
                    abbrevs[name] = words[0][:cur_len + 1]
                elif len(words) == 2:
                    abbrevs[name] = words[0][:2] + words[1][:2]
                else:
                    abbrevs[name] = words[0][:2] + ''.join(w[0] for w in words[1:] if w)

    # Final collision check — extend further if still colliding
    reverse = {}
    for name, abbr in abbrevs.items():
        reverse.setdefault(abbr, []).append(name)
    for abbr, names in reverse.items():
        if len(names) > 1:
            for i, name in enumerate(sorted(names)):
                if name in _MANUAL_ABBREVS:
                    continue
                if i > 0:
                    clean = name.lstrip('.')
                    words = [w for w in clean.split('_') if w]
                    abbrevs[name] = clean[:4]  # first 4 chars as fallback

    return abbrevs


# ── Filename Parsing ─────────────────────────

# Matches pigeon-compliant filenames
_PIGEON_RE = re.compile(
    r'^(?P<fullname>.+?)_seq(?P<seq>\d{3})_v(?P<ver>\d{3})'
    r'(?:_d(?P<date>\d{4}))?'
    r'(?:__(?P<slug>.+))?\.py$'
)

_LC_SEP = '_lc_'


def _parse_pigeon(filename):
    """Parse a pigeon-compliant filename into components."""
    m = _PIGEON_RE.match(filename)
    if not m:
        return None
    slug = m.group('slug') or ''
    desc = slug
    intent = ''
    if _LC_SEP in slug:
        desc, intent = slug.split(_LC_SEP, 1)
    return {
        'fullname': m.group('fullname'),
        'seq': m.group('seq'),
        'ver': m.group('ver'),
        'date': m.group('date') or '',
        'desc': desc,
        'intent': intent,
    }


def _extract_base_and_shard(fullname):
    """Split 'cognitive_reactor_seq014_api_client' into ('cognitive_reactor', 'api_client', '014').

    For non-shards like 'self_fix', returns ('self_fix', None, None).
    """
    # Check if fullname contains an intermediate _seq\d{3}_ (parent seq)
    shard_m = re.match(r'^(.+?)_seq(\d{3})_(.+)$', fullname)
    if shard_m:
        parent_base = shard_m.group(1)
        parent_seq = shard_m.group(2)
        shard_name = shard_m.group(3)
        return parent_base, shard_name, parent_seq
    return fullname, None, None


# ── Intent Lambda ────────────────────────────

def _intent_code(intent_str, intent_prefixes):
    """Convert intent string to lambda code. E.g. 'mutation_patch_pipeline' → 'λM'."""
    if not intent_str:
        return ''
    # Check known prefixes
    code = intent_prefixes.get(intent_str, '')
    if code:
        return code
    # Fallback: λ + first uppercase consonant of intent
    c = intent_str.replace('_', ' ').strip()
    if c:
        return 'λ' + c[0].upper()
    return ''


# ── Dep Glyphs ───────────────────────────────

def _dep_glyphs(mod_name, glyph_map, profiles, max_deps=3):
    """Get top partner glyphs for a module."""
    prof = profiles.get(mod_name, {})
    partners = prof.get('partners', [])
    own_glyph = glyph_map.get(mod_name, '')
    deps = []
    for p in partners:
        pname = p.get('name', '')
        g = glyph_map.get(pname, '')
        if g and g != own_glyph and g not in deps:
            deps.append(g)
        if len(deps) >= max_deps:
            break
    return ''.join(deps)


# ── New Filename Builder ─────────────────────

def _build_new_filename(parsed, base_name, shard_name, parent_seq,
                        glyph_map, abbrev_map, confidence, intent_prefixes, profiles):
    """Build the new abbreviated filename."""
    # Strip leading dot for glyph/confidence lookups
    lookup_name = base_name.lstrip('.')
    glyph = glyph_map.get(base_name, '') or glyph_map.get(lookup_name, '')
    state = _state_char(confidence, base_name) if base_name in confidence else _state_char(confidence, lookup_name)
    base_abbr = abbrev_map.get(base_name) or _MANUAL_ABBREVS.get(base_name) or abbrev_map.get(lookup_name) or _MANUAL_ABBREVS.get(lookup_name) or base_name[:3]

    seq = parsed['seq']
    ver = parsed['ver']
    date = parsed['date']
    intent = _intent_code(parsed['intent'], intent_prefixes)

    if shard_name:
        # Decomposed shard: 思p_cr_ac_s007_v002_d0322_λ7
        shard_words = [w for w in shard_name.replace('_decomposed', '').split('_') if w]
        shard_abbr = _abbreviate_word_list(shard_words)
        parts = [f'{glyph}{state}_{base_abbr}_{shard_abbr}_s{seq}_v{ver}']
    else:
        # Parent file: 修f_sf_s013_v011_d0328_叙算思_λM
        deps = _dep_glyphs(base_name, glyph_map, profiles)
        parts = [f'{glyph}{state}_{base_abbr}_s{seq}_v{ver}']

    if date:
        parts.append(f'd{date}')

    if not shard_name:
        deps = _dep_glyphs(base_name, glyph_map, profiles)
        if deps:
            parts.append(deps)

    if intent:
        parts.append(intent)

    return '_'.join(parts) + '.py'


def _build_new_dirname(base_name, parent_seq, glyph_map, abbrev_map):
    """Build new package directory name: 思_cr_s014"""
    glyph = glyph_map.get(base_name, '')
    abbr = abbrev_map.get(base_name, base_name[:3])
    if glyph:
        return f'{glyph}_{abbr}_s{parent_seq}'
    return f'{abbr}_s{parent_seq}'


# ── Scanner ──────────────────────────────────

SKIP_DIRS = {'.git', '__pycache__', 'node_modules', '.venv', 'venv',
             'pigeon_code.egg-info', '.mypy_cache', 'build', 'dist',
             'vscode-extension', 'chrome-extension', 'demo_logs', 'test_logs',
             'stress_logs', 'logs', 'docs', 'client'}

# Dirs within src/ that are decomposed packages
DECOMPOSED_PARENT_RE = re.compile(r'^\.?(\w+)_seq(\d{3})(?:_v\d+.*)?$')


def scan_all_renames(glyph_map, intent_prefixes, abbrev_map, confidence, profiles):
    """Build the complete rename plan: files and directories."""
    file_renames = []
    dir_renames = []

    # ── Scan decomposed package directories in src/ ──
    src = ROOT / 'src'
    if src.is_dir():
        for d in sorted(src.iterdir()):
            if not d.is_dir():
                continue
            dm = DECOMPOSED_PARENT_RE.match(d.name)
            if not dm:
                continue
            if d.name == '__pycache__':
                continue
            if d.name in _SKIP_DIR_NAMES:
                continue
            base_name = dm.group(1)
            pseq = dm.group(2)
            new_dname = _build_new_dirname(base_name, pseq, glyph_map, abbrev_map)
            if new_dname != d.name:
                dir_renames.append({
                    'old_path': str(d.relative_to(ROOT)).replace('\\', '/'),
                    'new_path': f'src/{new_dname}',
                    'old_name': d.name,
                    'new_name': new_dname,
                })

    # ── Scan all .py files ──
    for py in sorted(ROOT.rglob('*.py')):
        rel = py.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        # Skip files inside stale/broken directories
        if any(part in _SKIP_DIR_NAMES for part in rel.parts):
            continue
        if py.name == '__init__.py':
            continue
        if py.name.startswith('_') and not py.name.startswith('.'):
            # Skip infra scripts like _run_*, _build_*, _tmp_*
            if not _PIGEON_RE.match(py.name):
                continue
        if py.name.startswith('test_'):
            continue

        parsed = _parse_pigeon(py.name)
        if not parsed:
            continue

        base_name, shard_name, parent_seq = _extract_base_and_shard(parsed['fullname'])

        new_name = _build_new_filename(
            parsed, base_name, shard_name, parent_seq,
            glyph_map, abbrev_map, confidence, intent_prefixes, profiles,
        )

        # Determine new parent directory (if file is in a decomposed package)
        new_parent = py.parent
        for dr in dir_renames:
            if str(rel).replace('\\', '/').startswith(dr['old_path'] + '/'):
                new_parent = ROOT / dr['new_path']
                break

        new_path = new_parent / new_name
        new_rel = str(new_path.relative_to(ROOT)).replace('\\', '/')
        old_rel = str(rel).replace('\\', '/')

        if old_rel == new_rel:
            continue

        # MAX_PATH guard
        full_new = str(ROOT / new_rel)
        if len(full_new) > MAX_PATH:
            print(f'  [SKIP] path too long ({len(full_new)}): {old_rel}')
            continue

        # Validate identifier
        new_stem = new_name.removesuffix('.py')
        if not new_stem.isidentifier():
            print(f'  [SKIP] invalid identifier: {new_stem}')
            continue

        file_renames.append({
            'old_path': old_rel,
            'new_path': new_rel,
            'old_name': py.name,
            'new_name': new_name,
            'base': base_name,
        })

    return file_renames, dir_renames


# ── Execute ──────────────────────────────────

def execute_renames(file_renames, dir_renames, dry_run=True):
    total = len(file_renames) + len(dir_renames)
    if total == 0:
        print('Nothing to rename.')
        return

    mode = "DRY RUN" if dry_run else "EXECUTING"
    print(f'\n{mode}: {len(file_renames)} files + {len(dir_renames)} dirs\n')

    # Show sample
    print('── Directory renames ──')
    for d in dir_renames[:10]:
        print(f'  {d["old_name"]}  →  {d["new_name"]}')

    print(f'\n── File renames (first 30) ──')
    for r in file_renames[:30]:
        old_short = r['old_name'][:60]
        print(f'  {old_short:62s} →  {r["new_name"]}')
    if len(file_renames) > 30:
        print(f'  ... and {len(file_renames) - 30} more')

    if dry_run:
        print(f'\nDRY RUN — {total} renames planned. Use --execute to apply.')
        return

    # ── Step 1: Build import map (old_module → new_module) ──
    import_map = {}
    for r in file_renames:
        old_mod = r['old_path'].replace('/', '.').removesuffix('.py')
        new_mod = r['new_path'].replace('/', '.').removesuffix('.py')
        import_map[old_mod] = new_mod
    for d in dir_renames:
        import_map[d['old_path'].replace('/', '.')] = d['new_path'].replace('/', '.')

    # ── Step 2: Rewrite imports BEFORE moving files ──
    print(f'\n[1/4] Rewriting imports ({len(import_map)} mappings)...')
    rewrites = _rewrite_imports_inplace(import_map)
    print(f'      Rewrote {rewrites} import lines')

    # ── Step 3: Rename files ──
    print(f'[2/4] Renaming {len(file_renames)} files...')
    renamed_files = 0
    errors = []
    for i, r in enumerate(file_renames, 1):
        old = ROOT / r['old_path']
        new = ROOT / r['new_path']
        try:
            if not old.exists():
                errors.append(f'missing: {r["old_path"]}')
                continue
            new.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old), str(new))
            renamed_files += 1
            if i % 50 == 0:
                print(f'      ... {i}/{len(file_renames)}')
        except Exception as e:
            errors.append(f'{r["old_path"]}: {e}')
    print(f'      Renamed {renamed_files} files, {len(errors)} errors')

    # ── Step 4: Rename directories ──
    print(f'[3/4] Renaming {len(dir_renames)} directories...')
    for d in dir_renames:
        old_d = ROOT / d['old_path']
        new_d = ROOT / d['new_path']
        try:
            if old_d.exists():
                shutil.move(str(old_d), str(new_d))
                print(f'      {d["old_name"]} → {d["new_name"]}')
        except Exception as e:
            errors.append(f'dir {d["old_path"]}: {e}')

    # ── Step 5: Validate ──
    print(f'[4/4] Validating...')
    try:
        from pigeon_compiler.rename_engine.审p_va_s005_v004_d0315_踪稿析_λν import validate_imports
        val = validate_imports(ROOT)
        if val.get('valid'):
            print(f'      PASS — all imports valid')
        else:
            broken = val.get('broken', [])
            print(f'      WARNING: {len(broken)} broken imports')
            for b in broken[:10]:
                print(f'        {b}')
    except Exception as e:
        print(f'      [SKIP] validator failed: {e}')

    if errors:
        print(f'\nErrors ({len(errors)}):')
        for e in errors[:20]:
            print(f'  {e}')

    # Save rollback
    rb = {'file_renames': file_renames, 'dir_renames': dir_renames}
    rb_path = ROOT / 'logs' / 'smart_rename_rollback.json'
    rb_path.parent.mkdir(exist_ok=True)
    rb_path.write_text(json.dumps(rb, indent=2), encoding='utf-8')
    print(f'\nRollback saved: {rb_path.relative_to(ROOT)}')


def _rewrite_imports_inplace(import_map):
    """Rewrite all Python imports using the old→new module mapping.

    Processes longest paths first to avoid partial matches corrupting shard imports.
    """
    # Sort by key length descending — longest (most specific) paths first
    sorted_mappings = sorted(import_map.items(), key=lambda x: len(x[0]), reverse=True)
    count = 0
    for py in sorted(ROOT.rglob('*.py')):
        rel = py.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        try:
            text = py.read_text('utf-8', errors='ignore')
        except Exception:
            continue
        new_text = text
        for old_mod, new_mod in sorted_mappings:
            if old_mod in new_text:
                new_text = new_text.replace(old_mod, new_mod)
                count += 1
        if new_text != text:
            py.write_text(new_text, encoding='utf-8')
    return count


# ── Main ─────────────────────────────────────

def main():
    execute = '--execute' in sys.argv

    print('=== PIGEON SMART RENAME ===\n')

    print('Loading glyph + intent maps...')
    glyph_map, intent_prefixes = _load_glyph_map()
    print(f'  {len(glyph_map)} glyphs, {len(intent_prefixes)} intent codes')

    print('Loading registry...')
    reg_files = _load_registry()
    print(f'  {len(reg_files)} registered files')

    print('Loading confidence scores...')
    confidence = _load_confidence()
    print(f'  {len(confidence)} modules scored')

    print('Loading file profiles...')
    profiles = _load_profiles()
    print(f'  {len(profiles)} modules profiled')

    # Build abbreviation map from all unique base names (registry + disk)
    base_names = set()
    for f in reg_files:
        name = f['name']
        base, shard, _ = _extract_base_and_shard(name)
        base_names.add(base)
        if shard:
            pass

    # Also scan disk for modules not in registry
    for py in sorted(ROOT.rglob('*.py')):
        rel = py.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if any(part in _SKIP_DIR_NAMES for part in rel.parts):
            continue
        if py.name == '__init__.py' or py.name.startswith('test_'):
            continue
        parsed = _parse_pigeon(py.name)
        if not parsed:
            continue
        base, shard, _ = _extract_base_and_shard(parsed['fullname'])
        base_names.add(base)
        if shard:
            base_names.add(base)  # ensure parent is in map too

    print(f'\nBuilding abbreviations for {len(base_names)} base modules...')
    abbrev_map = build_abbreviation_map(base_names)

    # Show abbreviation map
    print('\n── Abbreviation Map (sample) ──')
    for name in sorted(abbrev_map)[:25]:
        print(f'  {name:40s} → {abbrev_map[name]}')
    if len(abbrev_map) > 25:
        print(f'  ... and {len(abbrev_map) - 25} more')

    # Check for any remaining collisions
    reverse = {}
    for name, abbr in abbrev_map.items():
        reverse.setdefault(abbr, []).append(name)
    collisions = {a: ns for a, ns in reverse.items() if len(ns) > 1}
    if collisions:
        print(f'\n⚠ {len(collisions)} collisions remain:')
        for abbr, names in collisions.items():
            print(f'  "{abbr}" ← {", ".join(names)}')

    print(f'\nScanning for renames...')
    file_renames, dir_renames = scan_all_renames(
        glyph_map, intent_prefixes, abbrev_map, confidence, profiles
    )

    # ── Check for filename collisions ──
    seen = {}
    collisions = []
    for r in file_renames:
        key = r['new_path']
        if key in seen:
            collisions.append((key, seen[key], r['old_path']))
        seen[key] = r['old_path']
    if collisions:
        print(f'\n⚠ {len(collisions)} FILENAME COLLISIONS (would overwrite!):')
        for new, old1, old2 in collisions[:20]:
            print(f'  {new}')
            print(f'    ← {old1}')
            print(f'    ← {old2}')
        if execute:
            print('ABORTING — fix collisions first.')
            return

    execute_renames(file_renames, dir_renames, dry_run=not execute)


if __name__ == '__main__':
    main()
