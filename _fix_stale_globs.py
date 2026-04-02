"""Fix stale _seq glob patterns left after smart rename.

Scans all .py files for patterns like 'logger_seq003*.py' or
'self_fix_seq013*' and replaces them with the new abbreviated
pattern like '*lo_s003*.py' or '*sf_s013*'.

Run: py _fix_stale_globs.py [--execute]
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# ── Build mapping from actual files on disk ──
# Scan all .py files and extract: old_name_prefix → new_abbreviation
# Old: logger_seq003_v005_d0322_...py  →  new: 録p_lo_s003_v005_d0322_...py
# Pattern key: "logger_seq003" → glob: "*lo_s003*"

def build_seq_map():
    """Build mapping: 'name_seq{N}' → '*abbrev_s{N}*' from renamed files on disk."""
    mapping = {}
    
    for py in ROOT.rglob('*.py'):
        name = py.stem
        # Match new-format files: {glyph}{state}_{abbrev}_s{seq}_v{ver}...
        m = re.match(r'^.+?[pfwu]_([a-z]+)_s(\d{3,4})_v', name)
        if not m:
            continue
        abbrev = m.group(1)
        seq_num = m.group(2)
        
        # Figure out what the old name was — reverse-map from the abbreviation
        # We need to find what old name had this seq number in this directory
        # Use the file's parent to scope
        rel = py.relative_to(ROOT)
        parts = list(rel.parts[:-1])  # directory parts
        
        # Store keyed by (directory, seq_num) to handle same seq in different dirs
        key = (tuple(parts), seq_num)
        if key not in mapping:
            mapping[key] = abbrev
    
    return mapping


def find_old_patterns():
    """Find all _seq\\d+\\* patterns in .py files."""
    # Match things like:
    #   'logger_seq003*.py'          → name=logger, seq=003
    #   'self_fix_seq013*.py'        → name=self_fix, seq=013
    #   'run_clean_split_seq010*.py' → name=run_clean_split, seq=010
    #   'prediction_scorer_seq014*'  → name=prediction_scorer, seq=014
    pattern = re.compile(r"""([a-z_]+)_seq(\d{3,4})\*""")
    
    hits = []
    for py in ROOT.rglob('*.py'):
        # Skip this script and __pycache__
        if py.name == '_fix_stale_globs.py':
            continue
        if '__pycache__' in str(py):
            continue
        
        try:
            text = py.read_text(encoding='utf-8')
        except (UnicodeDecodeError, PermissionError):
            continue
        
        for m in pattern.finditer(text):
            old_name = m.group(1)
            seq_num = m.group(2)
            hits.append({
                'file': py,
                'old_name': old_name,
                'seq_num': seq_num,
                'match_text': m.group(0),
                'start': m.start(),
                'end': m.end(),
            })
    
    return hits


def _build_disk_map():
    """Scan all .py files on disk and build: (old_base_name, seq_num) → abbreviation.
    
    Parses files matching the new format: {glyph}{state}_{abbrev}_s{seq}_v{ver}...
    Then reverse-maps from pigeon_registry.json to get the old base name.
    """
    import json as _json
    
    # First, build seq→abbreviation from disk
    seq_to_abbrev = {}  # (dir_tuple, seq_num) → abbrev
    for py in ROOT.rglob('*.py'):
        if '__pycache__' in str(py):
            continue
        m = re.match(r'^.+?[pfwu]_([a-z]+)_s(\d{3,4})_v', py.stem)
        if not m:
            continue
        abbrev = m.group(1)
        seq_num = m.group(2)
        rel_parts = tuple(py.relative_to(ROOT).parts[:-1])
        key = (rel_parts, seq_num)
        if key not in seq_to_abbrev:
            seq_to_abbrev[key] = abbrev
    
    # Load registry for old_name → seq mapping
    reg_path = ROOT / 'pigeon_registry.json'
    old_name_to_seq = {}
    if reg_path.exists():
        reg = _json.loads(reg_path.read_text('utf-8'))
        for key, info in reg.items():
            if not isinstance(info, dict):
                continue
            seq = info.get('seq')
            if seq is not None:
                old_name_to_seq[key] = str(seq).zfill(3)
    
    # Build: old_name → abbrev (using seq as bridge)
    result = {}
    for old_name, seq_num in old_name_to_seq.items():
        # Try finding in multiple directories
        for dir_tuple, abbrev in seq_to_abbrev.items():
            if dir_tuple == () or 'build' in dir_tuple:
                continue
            if seq_num == seq_to_abbrev.get((dir_tuple, seq_num), None) and seq_to_abbrev.get((dir_tuple, seq_num)):
                pass  # skip
            if (dir_tuple, seq_num) in seq_to_abbrev:
                result[(old_name, seq_num)] = seq_to_abbrev[(dir_tuple, seq_num)]
    
    # Also do a direct scan: for every seq on disk, just store seq→abbrev 
    # (simpler approach — seq numbers are unique within a directory context)
    simple_map = {}  # seq_num → set of abbrevs (usually 1)
    for (dir_tuple, seq_num), abbrev in seq_to_abbrev.items():
        if 'build' in dir_tuple:
            continue
        if seq_num not in simple_map:
            simple_map[seq_num] = {}
        # Key by directory prefix to disambiguate
        dir_key = '/'.join(dir_tuple) if dir_tuple else 'root'
        simple_map[seq_num][dir_key] = abbrev
    
    return simple_map


_DISK_MAP = None

def _get_disk_map():
    global _DISK_MAP
    if _DISK_MAP is None:
        _DISK_MAP = _build_disk_map()
    return _DISK_MAP


def infer_abbreviation(old_name, seq_num, context_dir=''):
    """Look up the actual abbreviation from files on disk."""
    disk_map = _get_disk_map()
    
    if seq_num in disk_map:
        abbrevs = disk_map[seq_num]
        # Try to match the context directory
        if context_dir and context_dir in abbrevs:
            return abbrevs[context_dir]
        # If only one option, use it
        if len(abbrevs) == 1:
            return list(abbrevs.values())[0]
        # Try common directories
        for try_dir in ['src', 'root', 'pigeon_brain/flow', 'pigeon_brain', 
                        'pigeon_compiler/runners', 'pigeon_compiler/rename_engine',
                        'pigeon_compiler/cut_executor']:
            if try_dir in abbrevs:
                return abbrevs[try_dir]
        # Just return the first one
        return list(abbrevs.values())[0]
    
    # Fallback: first letters of each word
    parts = old_name.split('_')
    if len(parts) == 1:
        return old_name[:3]
    return ''.join(p[0] for p in parts if p)


def build_replacement(old_name, seq_num, match_text, context_dir=''):
    """Build the replacement glob pattern."""
    abbrev = infer_abbreviation(old_name, seq_num, context_dir)
    
    # If original had .py suffix, keep it
    if match_text.endswith('*.py'):
        return f'*{abbrev}_s{seq_num}*.py'
    else:
        return f'*{abbrev}_s{seq_num}*'


def main():
    execute = '--execute' in sys.argv
    
    hits = find_old_patterns()
    
    if not hits:
        print("No stale _seq glob patterns found!")
        return
    
    # Group by file
    from collections import defaultdict
    by_file = defaultdict(list)
    for h in hits:
        by_file[h['file']].append(h)
    
    print(f"Found {len(hits)} stale patterns in {len(by_file)} files\n")
    
    total_replaced = 0
    
    for filepath, file_hits in sorted(by_file.items()):
        rel = filepath.relative_to(ROOT)
        print(f"  {rel}:")
        
        text = filepath.read_text(encoding='utf-8')
        
        for h in file_hits:
            old = h['match_text']
            # Determine context dir from the glob pattern in the source
            # e.g. root.glob('src/self_fix_seq013*.py') → context is 'src'
            # or _load_pigeon_module(root, 'pigeon_brain/flow', 'prediction_scorer_seq014*') → 'pigeon_brain/flow'
            ctx = ''
            # Try to extract dir from the surrounding code
            line_start = text.rfind('\n', 0, h['start']) + 1
            line_end = text.find('\n', h['end'])
            line = text[line_start:line_end] if line_end > 0 else text[line_start:]
            # Look for directory hints in the line
            dir_m = re.search(r"['\"]([a-z_/]+)/[a-z_]+_seq\d+", line)
            if dir_m:
                ctx = dir_m.group(1)
            new = build_replacement(h['old_name'], h['seq_num'], old, ctx)
            
            # Also handle the error message variant
            count = text.count(old)
            print(f"    {old:45s} → {new:25s} ({count} occurrences)")
            
            if execute:
                text = text.replace(old, new)
                total_replaced += count
        
        if execute:
            filepath.write_text(text, encoding='utf-8')
    
    if execute:
        print(f"\n✓ Replaced {total_replaced} patterns across {len(by_file)} files")
    else:
        print(f"\n  DRY RUN — use --execute to apply {len(hits)} replacements")


if __name__ == '__main__':
    main()
