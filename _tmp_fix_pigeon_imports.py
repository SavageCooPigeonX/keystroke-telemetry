"""Fix hardcoded pigeon imports in pigeon_brain/ files.

Maps old long-form names to current short pigeon filenames using seq matching.
"""
import re
from pathlib import Path

root = Path('.')

def find_current_file(pkg_dir: Path, old_name: str):
    """Find current file matching old_name's seq number."""
    # Extract seq from old name: e.g. graph_extractor_seq003 from .graph_extractor_seq003_v003_d0324__...
    m = re.match(r'\.?(\w+_seq\d+)', old_name)
    if not m:
        return None
    seq_base = m.group(1)  # e.g. graph_extractor_seq003
    # Also try just the seq number
    seq_m = re.search(r'seq(\d+)', old_name)
    if not seq_m:
        return None
    seq_num = seq_m.group(1)
    
    # Search for files in pkg_dir matching this seq
    candidates = []
    for f in pkg_dir.glob('*.py'):
        if f.name == '__init__.py':
            continue
        if f'_s{seq_num}_' in f.name or f'seq{seq_num}' in f.name:
            candidates.append(f)
    
    if len(candidates) == 1:
        return candidates[0]
    elif len(candidates) > 1:
        # Pick the one with highest version
        best = max(candidates, key=lambda f: f.name)
        return best
    return None

def fix_file(py_path: Path):
    """Fix hardcoded imports in a single file."""
    text = py_path.read_text('utf-8')
    lines = text.split('\n')
    new_lines = []
    changes = []
    pkg_dir = py_path.parent
    
    for line in lines:
        stripped = line.lstrip()
        # Match: from .old_long_name import ...
        m = re.match(r'^(\s*from\s+)(\.\w+_seq\d+_v\d+_d\d+\S+)(\s+import\s+.+)$', stripped)
        if m:
            indent = line[:len(line) - len(stripped)]
            prefix = m.group(1)
            old_mod = m.group(2)
            suffix = m.group(3)
            
            current = find_current_file(pkg_dir, old_mod)
            if current:
                new_mod = '.' + current.stem
                new_line = indent + prefix + new_mod + suffix
                if new_line.rstrip() != line.rstrip():
                    changes.append((line.strip(), new_line.strip()))
                    new_lines.append(new_line)
                    continue
        
        new_lines.append(line)
    
    if changes:
        new_text = '\n'.join(new_lines)
        py_path.write_text(new_text, 'utf-8')
        return changes
    return []

# Process pigeon_brain/ files
total_fixes = 0
for py in sorted(root.joinpath('pigeon_brain').rglob('*.py')):
    if '__pycache__' in str(py) or py.name == '__init__.py':
        continue
    changes = fix_file(py)
    if changes:
        rel = py.relative_to(root)
        print(f'{rel}: {len(changes)} fixes')
        for old, new in changes:
            print(f'  - {old[:80]}')
            print(f'  + {new[:80]}')
        total_fixes += len(changes)

print(f'\nTotal fixes applied: {total_fixes}')
