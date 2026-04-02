"""Quick spot-check of src/ file renames."""
import sys
sys.path.insert(0, '.')
from _run_smart_rename import (_load_glyph_map, _load_registry, _load_confidence,
    _load_profiles, _extract_base_and_shard, build_abbreviation_map, scan_all_renames,
    _parse_pigeon, _SKIP_DIR_NAMES, SKIP_DIRS)

glyph_map, intent_prefixes = _load_glyph_map()
reg_files = _load_registry()
confidence = _load_confidence()
profiles = _load_profiles()
from pathlib import Path
ROOT = Path('.').resolve()
base_names = set()
for f in reg_files:
    base, shard, _ = _extract_base_and_shard(f['name'])
    base_names.add(base)
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

abbrev_map = build_abbreviation_map(base_names)
file_renames, dir_renames = scan_all_renames(glyph_map, intent_prefixes, abbrev_map, confidence, profiles)

# Check for filename collisions
seen = {}
for r in file_renames:
    key = r['new_path']
    if key in seen:
        print(f"COLLISION: {key}")
        print(f"  <- {seen[key]}")
        print(f"  <- {r['old_path']}")
    seen[key] = r['old_path']

# Show key modules
KEY_BASES = ['self_fix', 'cognitive_reactor', 'dynamic_prompt', 'copilot_prompt_manager',
             'prompt_journal', 'push_cycle', 'streaming_layer', 'symbol_dictionary']
print("\n── KEY MODULE RENAMES ──")
for r in file_renames:
    if r['base'] in KEY_BASES and r['old_path'].startswith('src/') and r['old_path'].count('/') <= 1:
        print(f"  {r['new_name']:50s} <- {r['base']}")

