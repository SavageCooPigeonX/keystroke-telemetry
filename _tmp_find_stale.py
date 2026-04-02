"""Find all stale _seqNNN glob patterns and fix them to match new _sNNN filenames."""
import re
from pathlib import Path

root = Path('.')

# Step 1: Build per-directory seq->stem mapping from actual disk filenames
# New format: 修f_sf_s013_v011_d0328_... has _s013_
# Old globs: self_fix_seq013* has _seq013

S_PAT = re.compile(r'_s(\d{3,4})_v')

dir_seq_map = {}  # (dir_path, seq) -> filename stem

SCAN_DIRS = [
    '.', 'src', 'src/cognitive', 'pigeon_brain', 'pigeon_brain/flow',
    'pigeon_compiler', 'pigeon_compiler/rename_engine', 'pigeon_compiler/runners',
    'pigeon_compiler/cut_executor', 'pigeon_compiler/state_extractor',
    'pigeon_compiler/bones', 'pigeon_compiler/integrations',
    'pigeon_compiler/weakness_planner',
    'pigeon_compiler/runners/compiler_output/press_release_gen',
    'streaming_layer', 'client', 'vscode-extension',
]

for d in SCAN_DIRS:
    dp = root / d
    if not dp.exists():
        continue
    for f in sorted(dp.glob('*.py')):
        if f.name == '__init__.py':
            continue
        m = S_PAT.search(f.stem)
        if m:
            seq = m.group(1)
            rel_dir = str(dp.relative_to(root)).replace('\\', '/')
            if rel_dir == '.':
                rel_dir = ''
            dir_seq_map[(rel_dir, seq)] = f.stem

# Also scan decomposed package dirs
for parent_dir in ['src', 'pigeon_brain/flow', 'pigeon_compiler/runners']:
    pp = root / parent_dir
    if not pp.exists():
        continue
    for pkg in pp.iterdir():
        if pkg.is_dir() and not pkg.name.startswith('_') and pkg.name != '__pycache__':
            for f in sorted(pkg.glob('*.py')):
                if f.name == '__init__.py':
                    continue
                m = S_PAT.search(f.stem)
                if m:
                    seq = m.group(1)
                    rel = str(pkg.relative_to(root)).replace('\\', '/')
                    dir_seq_map[(rel, seq)] = f.stem

print(f'Disk seq map: {len(dir_seq_map)} entries')
for k in sorted(dir_seq_map.keys())[:10]:
    print(f'  {k} -> {dir_seq_map[k][:60]}')
print('  ...')

# Step 2: Find stale patterns and compute replacements
stale_pattern = re.compile(r"""(['"])([a-z_/]*?)([a-z][a-z_]+)_seq(\d{3,4})\*""")

SKIP_FILES = {'_tmp_', '_run_', '_fix_', 'stress_', 'autonomous_', 'deep_test', '_build_', '_export_'}

replacements = []  # (filepath, old_text, new_text)
unresolved = []

for py in sorted(root.rglob('*.py')):
    rel = str(py.relative_to(root)).replace('\\', '/')
    if any(skip in rel for skip in ['__pycache__', '.venv', 'node_modules', '.egg-info', 'build']):
        continue
    if any(rel.split('/')[-1].startswith(p) for p in SKIP_FILES):
        continue
    try:
        text = py.read_text('utf-8')
    except:
        continue

    matches = list(stale_pattern.finditer(text))
    if not matches:
        continue

    # Determine the file's own directory
    file_dir = str(py.parent.relative_to(root)).replace('\\', '/')
    if file_dir == '.':
        file_dir = ''

    for m in matches:
        quote = m.group(1)
        dir_prefix = m.group(2).rstrip('/')
        old_name = m.group(3)
        seq = m.group(4)

        # Determine target directory
        if dir_prefix:
            target_dir = dir_prefix
        else:
            target_dir = file_dir

        # Look up in our map
        key = (target_dir, seq)
        new_stem = dir_seq_map.get(key)

        if not new_stem:
            # Try parent dir
            parent = '/'.join(target_dir.split('/')[:-1]) if '/' in target_dir else ''
            key2 = (parent, seq)
            new_stem = dir_seq_map.get(key2)

        if not new_stem and target_dir != 'src':
            # Try src
            new_stem = dir_seq_map.get(('src', seq))

        if not new_stem and target_dir.startswith('src/cognitive'):
            new_stem = dir_seq_map.get(('src/cognitive', seq))

        if new_stem:
            # Build the new glob: take everything up to _sNNN
            m2 = re.search(r'(_s\d{3,4})_', new_stem)
            if m2:
                new_glob_base = new_stem[:m2.end()-1]
            else:
                new_glob_base = new_stem

            old_full = f'{dir_prefix + "/" if dir_prefix else ""}{old_name}_seq{seq}*'
            new_full = f'{dir_prefix + "/" if dir_prefix else ""}{new_glob_base}*'
            replacements.append((rel, f'{quote}{old_full}', f'{quote}{new_full}'))
            print(f'  OK {rel}: {old_full} -> {new_full}')
        else:
            old_full = f'{dir_prefix + "/" if dir_prefix else ""}{old_name}_seq{seq}*'
            unresolved.append((rel, old_full, target_dir, seq))
            print(f'  ?? {rel}: {old_full} (dir={target_dir}, seq={seq})')

print(f'\n{len(replacements)} resolved, {len(unresolved)} unresolved')

# Step 3: Apply replacements
if unresolved:
    print('\nUnresolved refs - need manual fix:')
    for rel, pat, tdir, seq in unresolved:
        print(f'  {rel}: {pat}')
    print()

if replacements:
    print('\nApplying replacements...')
    changed_files = set()
    for rel, old_text, new_text in replacements:
        fpath = root / rel
        text = fpath.read_text('utf-8')
        if old_text in text:
            text = text.replace(old_text, new_text)
            fpath.write_text(text, 'utf-8')
            changed_files.add(rel)
            print(f'  Fixed: {rel}: {old_text} -> {new_text}')
        else:
            print(f'  SKIP (not found): {rel}: {old_text}')
    print(f'\nDone. Changed {len(changed_files)} files.')
