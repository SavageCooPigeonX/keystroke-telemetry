"""Abbreviated rename — compress pigeon filenames keeping ALL metadata.

Current: cognitive_reactor_seq014_v005_d0331__思算研测_cognitive_reactor_autonomous_code_modification_lc_mutation_patch_pipeline.py
New:     思_cr_s14v5_d0331_算研测_mpp.py

Decomposed shard:
Current: cognitive_reactor_seq014_api_client_seq007_v002.py
New:     思_cr_s14_ac_s7v2.py

Format: {glyph}_{abbrev}_s{seq}v{ver}_d{date}_{dep_glyphs}_{lc_abbrev}.py
All metadata preserved, just abbreviated. Filenames become a living debug layer.
"""
import json
import os
import re
from collections import Counter
from pathlib import Path

ROOT = Path('.')
DIRS = ['src', 'pigeon_compiler', 'pigeon_brain', 'streaming_layer']

# ── Step 1: Parse all pigeon filenames ──

def parse_pigeon_name(stem: str) -> dict | None:
    """Parse a pigeon filename into its component parts."""
    # Skip non-pigeon files
    if stem.startswith('_') or stem.startswith('__') or stem in ('_resolve', 'cli', 'git_plugin', 'session_logger', 'pigeon_limits', 'pre_commit_audit'):
        return None

    # Pattern 1: Full pigeon name with glyph + desc + intent
    # {name}_seq{N}_v{V}_d{MMDD}__{glyphs}_{desc}_lc_{intent}.py
    m = re.match(
        r'^(?P<name>.+?)_seq(?P<seq>\d+)_v(?P<ver>\d+)_d(?P<date>\d{4})__(?P<glyphs>[^\x00-\x7F]+)_(?P<desc>.+?)_lc_(?P<intent>.+)$',
        stem
    )
    if m:
        return {
            'type': 'full',
            'name': m.group('name'),
            'seq': int(m.group('seq')),
            'ver': int(m.group('ver')),
            'date': m.group('date'),
            'glyphs': m.group('glyphs'),
            'desc': m.group('desc'),
            'intent': m.group('intent'),
        }

    # Pattern 2: Pigeon name with glyphs but no desc/intent (e.g., decomposed shards with glyphs)
    # {name}_seq{N}_{shard}_seq{M}_v{V}_d{MMDD}__{glyphs}_{desc}_lc_{intent}.py
    m = re.match(
        r'^(?P<parent>.+?)_seq(?P<pseq>\d+)_(?P<shard>.+?)_seq(?P<sseq>\d+)_v(?P<ver>\d+)_d(?P<date>\d{4})__(?P<glyphs>[^\x00-\x7F]+)_(?P<desc>.+?)_lc_(?P<intent>.+)$',
        stem
    )
    if m:
        return {
            'type': 'decomposed_full',
            'parent': m.group('parent'),
            'parent_seq': int(m.group('pseq')),
            'shard': m.group('shard'),
            'shard_seq': int(m.group('sseq')),
            'ver': int(m.group('ver')),
            'date': m.group('date'),
            'glyphs': m.group('glyphs'),
            'desc': m.group('desc'),
            'intent': m.group('intent'),
        }

    # Pattern 3: Decomposed shard (no glyphs, no date)
    # {parent}_seq{N}_{shard}_seq{M}_v{V}.py
    m = re.match(
        r'^(?P<parent>.+?)_seq(?P<pseq>\d+)_(?P<shard>.+?)_seq(?P<sseq>\d+)_v(?P<ver>\d+)$',
        stem
    )
    if m:
        return {
            'type': 'decomposed_bare',
            'parent': m.group('parent'),
            'parent_seq': int(m.group('pseq')),
            'shard': m.group('shard'),
            'shard_seq': int(m.group('sseq')),
            'ver': int(m.group('ver')),
        }

    # Pattern 4: Decomposed shard with glyphs but no date/desc
    # {parent}_seq{N}_{shard}_seq{M}_v{V}_d{MMDD}__{glyphs}.py
    m = re.match(
        r'^(?P<parent>.+?)_seq(?P<pseq>\d+)_(?P<shard>.+?)_seq(?P<sseq>\d+)_v(?P<ver>\d+)_d(?P<date>\d{4})__(?P<rest>.+)$',
        stem
    )
    if m:
        rest = m.group('rest')
        # Check if rest is just glyphs or has desc
        if re.match(r'^[^\x00-\x7F]+$', rest):
            return {
                'type': 'decomposed_glyph',
                'parent': m.group('parent'),
                'parent_seq': int(m.group('pseq')),
                'shard': m.group('shard'),
                'shard_seq': int(m.group('sseq')),
                'ver': int(m.group('ver')),
                'date': m.group('date'),
                'glyphs': rest,
            }

    # Pattern 5: Bare pigeon name (just name + seq + ver, no date/desc)
    # {name}_seq{N}_v{V}.py
    m = re.match(
        r'^(?P<name>.+?)_seq(?P<seq>\d+)_v(?P<ver>\d+)$',
        stem
    )
    if m:
        return {
            'type': 'bare',
            'name': m.group('name'),
            'seq': int(m.group('seq')),
            'ver': int(m.group('ver')),
        }

    # Pattern 6: Has date but no double-underscore section
    m = re.match(
        r'^(?P<name>.+?)_seq(?P<seq>\d+)_v(?P<ver>\d+)_d(?P<date>\d{4})$',
        stem
    )
    if m:
        return {
            'type': 'dated',
            'name': m.group('name'),
            'seq': int(m.group('seq')),
            'ver': int(m.group('ver')),
            'date': m.group('date'),
        }

    return None


# ── Step 2: Build abbreviation map with collision detection ──

def build_abbreviation(name: str) -> str:
    """Build an abbreviation from a module name."""
    # Strip leading Chinese chars
    clean = re.sub(r'^[^\x00-\x7F]+_?', '', name).lstrip('.')

    parts = clean.split('_')
    if len(parts) == 1:
        word = parts[0]
        if len(word) <= 3:
            return word
        return word[:2]

    # First letter of each word
    return ''.join(p[0] for p in parts if p)


def build_abbreviation_map(names: list[str]) -> dict[str, str]:
    """Build a collision-free abbreviation map."""
    # First pass: generate initial abbreviations
    abbrevs = {}
    for name in sorted(set(names)):
        abbrevs[name] = build_abbreviation(name)

    # Detect collisions
    rev = {}
    for name, abbr in abbrevs.items():
        rev.setdefault(abbr, []).append(name)

    # Resolve collisions
    for abbr, colliders in rev.items():
        if len(colliders) <= 1:
            continue
        # Try progressively longer abbreviations
        for name in colliders:
            clean = re.sub(r'^[^\x00-\x7F]+_?', '', name).lstrip('.')
            parts = clean.split('_')
            # Try: first letter of first word + first 2 letters of second
            if len(parts) >= 2:
                candidate = parts[0][0] + parts[1][:2]
                abbrevs[name] = candidate
            else:
                abbrevs[name] = clean[:3]

        # Check again for remaining collisions
        vals = [abbrevs[n] for n in colliders]
        if len(vals) != len(set(vals)):
            # Still colliding — use more chars
            for name in colliders:
                clean = re.sub(r'^[^\x00-\x7F]+_?', '', name).lstrip('.')
                parts = clean.split('_')
                if len(parts) >= 2:
                    abbrevs[name] = parts[0][:2] + parts[1][0]
                else:
                    abbrevs[name] = clean[:4]

    return abbrevs


def abbreviate_intent(intent: str) -> str:
    """Abbreviate an intent string to 2-4 chars."""
    if not intent:
        return ''
    parts = intent.split('_')
    # First letter of each word, max 4
    return ''.join(p[0] for p in parts[:4] if p)


# ── Step 3: Extract glyph mapping from current filenames ──

def extract_glyph_map(dirs: list[str]) -> dict[str, str]:
    """Extract module name → Chinese glyph from existing filenames."""
    gmap = {}
    for d in dirs:
        p = ROOT / d
        if not p.exists():
            continue
        for f in p.rglob('*.py'):
            m = re.match(
                r'^(.+?)_seq\d+_v\d+_d\d{4}__([^\x00-\x7F]+)_',
                f.stem
            )
            if m:
                name = m.group(1)
                glyphs = m.group(2)
                clean = re.sub(r'^[^\x00-\x7F]+_?', '', name).lstrip('.')
                if clean not in gmap and glyphs:
                    gmap[clean] = glyphs[0]

    return gmap


# ── Step 4: Generate new filenames ──

def new_filename(parsed: dict, abbrev_map: dict, glyph_map: dict) -> str:
    """Generate abbreviated filename from parsed components."""
    typ = parsed['type']

    if typ == 'full':
        name = re.sub(r'^[^\x00-\x7F]+_?', '', parsed['name']).lstrip('.')
        glyph = glyph_map.get(name, '')
        abbr = abbrev_map.get(name, name[:3])
        seq = parsed['seq']
        ver = parsed['ver']
        date = parsed['date']
        glyphs = parsed['glyphs']
        # dep_glyphs = all chars after the first (which is the module's own)
        dep_glyphs = glyphs[1:] if len(glyphs) > 1 else ''
        lc = abbreviate_intent(parsed['intent'])
        parts = [glyph, abbr, f's{seq}v{ver}', f'd{date}']
        if dep_glyphs:
            parts.append(dep_glyphs)
        if lc:
            parts.append(lc)
        return '_'.join(parts)

    if typ in ('decomposed_full', 'decomposed_glyph'):
        parent = re.sub(r'^[^\x00-\x7F]+_?', '', parsed['parent']).lstrip('.')
        glyph = glyph_map.get(parent, '')
        p_abbr = abbrev_map.get(parent, parent[:3])
        p_seq = parsed['parent_seq']
        shard = parsed['shard']
        s_abbr = abbrev_map.get(shard, build_abbreviation(shard))
        s_seq = parsed['shard_seq']
        ver = parsed['ver']
        parts = [glyph, p_abbr, f's{p_seq}', s_abbr, f's{s_seq}v{ver}']
        if parsed.get('date'):
            parts.append(f'd{parsed["date"]}')
        dep_glyphs = parsed.get('glyphs', '')[1:] if len(parsed.get('glyphs', '')) > 1 else ''
        if dep_glyphs:
            parts.append(dep_glyphs)
        if parsed.get('intent'):
            parts.append(abbreviate_intent(parsed['intent']))
        return '_'.join(parts)

    if typ == 'decomposed_bare':
        parent = re.sub(r'^[^\x00-\x7F]+_?', '', parsed['parent']).lstrip('.')
        glyph = glyph_map.get(parent, '')
        p_abbr = abbrev_map.get(parent, parent[:3])
        p_seq = parsed['parent_seq']
        shard = parsed['shard']
        s_abbr = abbrev_map.get(shard, build_abbreviation(shard))
        s_seq = parsed['shard_seq']
        ver = parsed['ver']
        parts = [glyph, p_abbr, f's{p_seq}', s_abbr, f's{s_seq}v{ver}']
        return '_'.join(parts)

    if typ == 'bare':
        name = re.sub(r'^[^\x00-\x7F]+_?', '', parsed['name']).lstrip('.')
        glyph = glyph_map.get(name, '')
        abbr = abbrev_map.get(name, name[:3])
        seq = parsed['seq']
        ver = parsed['ver']
        parts = [glyph, abbr, f's{seq}v{ver}']
        return '_'.join(parts)

    if typ == 'dated':
        name = re.sub(r'^[^\x00-\x7F]+_?', '', parsed['name']).lstrip('.')
        glyph = glyph_map.get(name, '')
        abbr = abbrev_map.get(name, name[:3])
        seq = parsed['seq']
        ver = parsed['ver']
        date = parsed['date']
        parts = [glyph, abbr, f's{seq}v{ver}', f'd{date}']
        return '_'.join(parts)

    return None


# ── Step 5: Main orchestrator ──

def run_rename(dry_run: bool = True):
    """Execute the abbreviated rename across the codebase."""
    # Collect all pigeon files
    all_files = []
    all_names = set()
    shard_names = set()

    for d in DIRS:
        p = ROOT / d
        if not p.exists():
            continue
        for f in p.rglob('*.py'):
            parsed = parse_pigeon_name(f.stem)
            if parsed:
                all_files.append((f, parsed))
                if parsed['type'] in ('full', 'bare', 'dated'):
                    name = re.sub(r'^[^\x00-\x7F]+_?', '', parsed['name']).lstrip('.')
                    all_names.add(name)
                elif 'parent' in parsed:
                    parent = re.sub(r'^[^\x00-\x7F]+_?', '', parsed['parent']).lstrip('.')
                    all_names.add(parent)
                    shard_names.add(parsed['shard'])

    # Build maps
    all_module_names = list(all_names | shard_names)
    abbrev_map = build_abbreviation_map(all_module_names)
    glyph_map = extract_glyph_map(DIRS)

    # Print abbreviation map
    print("=== ABBREVIATION MAP ===")
    for name in sorted(abbrev_map):
        g = glyph_map.get(name, ' ')
        print(f"  {g} {name} → {abbrev_map[name]}")

    # Check for collisions
    rev = {}
    for n, a in abbrev_map.items():
        rev.setdefault(a, []).append(n)
    collisions = {a: ns for a, ns in rev.items() if len(ns) > 1}
    if collisions:
        print("\n⚠️ COLLISIONS:")
        for a, ns in collisions.items():
            print(f"  '{a}' ← {ns}")
        print("Fix collisions before running!")
        return

    # Generate renames
    renames = []
    skipped = 0
    for f, parsed in all_files:
        new_stem = new_filename(parsed, abbrev_map, glyph_map)
        if new_stem is None:
            skipped += 1
            continue
        new_path = f.parent / (new_stem + f.suffix)
        if f == new_path:
            continue
        renames.append((f, new_path))

    print(f"\n=== RENAME PLAN: {len(renames)} files (skipped {skipped}) ===")
    # Show samples per directory
    by_dir = {}
    for old, new in renames:
        d = str(old.parent)
        by_dir.setdefault(d, []).append((old, new))

    for d in sorted(by_dir):
        print(f"\n📁 {d} ({len(by_dir[d])} files)")
        for old, new in by_dir[d][:5]:
            print(f"  {old.name}")
            print(f"  → {new.name}")

        if len(by_dir[d]) > 5:
            print(f"  ... and {len(by_dir[d]) - 5} more")

    if dry_run:
        print("\n🏜️ DRY RUN — no files changed. Run with dry_run=False to execute.")
        return renames

    # Execute renames
    print("\n🔧 EXECUTING RENAMES...")
    done = 0
    errors = []
    for old, new in renames:
        try:
            os.rename(old, new)
            done += 1
        except Exception as e:
            errors.append((old, new, str(e)))

    print(f"✅ Renamed {done}/{len(renames)} files")
    if errors:
        print(f"\n❌ {len(errors)} errors:")
        for old, new, err in errors:
            print(f"  {old} → {err}")

    # Update _resolve.py files
    update_resolvers(renames)

    # Update __init__.py files
    update_inits(renames)

    return renames


def update_resolvers(renames: list):
    """Update _resolve.py files to handle new filename format."""
    # Group renames by directory
    dirs_affected = set()
    for old, new in renames:
        dirs_affected.add(old.parent)

    for d in dirs_affected:
        resolve = d / '_resolve.py'
        if not resolve.exists():
            continue

        text = resolve.read_text(encoding='utf-8')

        # The resolver matches: ^{prefix}_v\d+
        # We need to add a fallback that matches the new abbreviated format
        # by extracting the seq number and searching for _s{N}v\d+
        if '_find_abbreviated' not in text:
            # Inject the abbreviated format handler
            inject = '''

def _find_abbreviated(seq_prefix: str, search_dir) -> str | None:
    """Find module by seq number in abbreviated filename format.
    
    Old callers pass 'logger_seq003' — this extracts seq=3 and searches
    for files containing '_s3v' in the search directory.
    """
    m = re.match(r'(\\w+)_seq(\\d+)', seq_prefix)
    if not m:
        return None
    seq_n = str(int(m.group(2)))  # strip leading zeros
    pat = re.compile(rf'_s{seq_n}v\\d+')
    for child in search_dir.iterdir():
        if child.is_dir() and (child / '__init__.py').exists():
            if pat.search(child.name):
                return child.name
    for child in search_dir.iterdir():
        if child.suffix == '.py' and pat.search(child.stem):
            return child.stem
    return None
'''
            # Insert before the main _find_module function
            text = text.replace(
                'def _find_module(',
                inject + '\ndef _find_module('
            )

            # Add fallback call at end of _find_module
            text = text.replace(
                '    return None\n\n\ndef src_import',
                '    # Fallback: try abbreviated format\n'
                '    return _find_abbreviated(seq_prefix, _SRC_DIR)\n\n\ndef src_import'
            )

            resolve.write_text(text, encoding='utf-8')
            print(f"  Updated {resolve}")


def update_inits(renames: list):
    """Update __init__.py files with new import paths."""
    dirs_affected = set()
    # Build old_stem → new_stem map
    stem_map = {}
    for old, new in renames:
        stem_map[old.stem] = new.stem
        dirs_affected.add(old.parent)

    for d in dirs_affected:
        init = d / '__init__.py'
        if not init.exists():
            continue

        text = init.read_text(encoding='utf-8')
        changed = False
        for old_stem, new_stem in stem_map.items():
            if old_stem in text:
                text = text.replace(old_stem, new_stem)
                changed = True

        if changed:
            init.write_text(text, encoding='utf-8')
            print(f"  Updated {init}")


if __name__ == '__main__':
    import sys
    dry = '--execute' not in sys.argv
    run_rename(dry_run=dry)
