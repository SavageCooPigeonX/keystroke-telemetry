"""Fix all broken __init__.py files across the project.

Scans every __init__.py, checks if its imports reference files that don't exist,
then rebuilds the init from actual existing files and their public exports.
"""
import ast
import pathlib
import re

ROOT = pathlib.Path('.')
DIRS = ['src', 'pigeon_compiler', 'pigeon_brain', 'streaming_layer']


def get_public_exports(file_path):
    """Extract public function/class names from a .py file."""
    try:
        tree = ast.parse(file_path.read_text('utf-8'))
    except Exception:
        return []
    exports = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith('_'):
                exports.append(node.name)
        elif isinstance(node, ast.ClassDef):
            if not node.name.startswith('_'):
                exports.append(node.name)
    return exports


def get_imported_names(init_text):
    """Extract module names referenced in from-imports."""
    names = set()
    for line in init_text.splitlines():
        # from .module_name import ...
        m = re.match(r'from\s+\.(\w+)\s+import', line)
        if m:
            names.add(m.group(1))
        # from package.module_name import ... (absolute)
        m = re.match(r'from\s+\w+\.(\w+)\s+import', line)
        if m:
            names.add(m.group(1))
        # from ..module_name import ... (parent relative)
        m = re.match(r'from\s+\.\.(\w+)\s+import', line)
        if m:
            names.add(m.group(1))
    return names


def rebuild_init(pkg_dir, existing_modules):
    """Build a new __init__.py from actual existing files."""
    lines = [f'"""{pkg_dir.name}/ -- auto-fixed pigeon package."""']
    total_exports = 0
    for mod_name in sorted(existing_modules):
        mod_file = pkg_dir / f'{mod_name}.py'
        exports = get_public_exports(mod_file)
        if exports:
            lines.append(f'from .{mod_name} import {", ".join(exports)}')
            total_exports += len(exports)
    return '\n'.join(lines) + '\n', total_exports


def fix_init(init_path):
    """Fix a single __init__.py. Returns (fixed, detail)."""
    txt = init_path.read_text('utf-8')
    pkg_dir = init_path.parent
    
    # Get existing importable files (no dot prefix, no __init__)
    existing = {f.stem for f in pkg_dir.glob('*.py')
                if f.name != '__init__.py' and not f.name.startswith('.')}
    
    # Check for dot-prefixed files (un-importable)
    dot_files = [f for f in pkg_dir.glob('*.py')
                 if f.name.startswith('.') and f.name != '__init__.py']
    
    if not existing and dot_files:
        init_path.write_text(
            '# dot-prefixed files not importable by Python\n',
            encoding='utf-8')
        return True, 'dot-prefix package'
    
    if not existing:
        if txt.strip() and len(txt) > 80:
            init_path.write_text(
                '# empty package - shards removed or relocated\n',
                encoding='utf-8')
            return True, 'emptied stale init'
        return False, 'already empty'
    
    # Check if imports are broken
    imported = get_imported_names(txt)
    missing = imported - existing
    
    if not missing:
        return False, 'imports OK'
    
    # Rebuild from actual files
    new_init, n_exports = rebuild_init(pkg_dir, existing)
    init_path.write_text(new_init, encoding='utf-8')
    return True, f'{n_exports} exports from {len(existing)} files'


def main():
    fixed = 0
    checked = 0
    
    for d in DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for init in sorted(base.rglob('__init__.py')):
            checked += 1
            was_fixed, detail = fix_init(init)
            if was_fixed:
                fixed += 1
                print(f'  FIXED {init}: {detail}')

    # Also fix broken relative imports in non-init files
    print('\n--- fixing internal relative imports ---')
    fixed_internal = 0
    for d in DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for py in sorted(base.rglob('*.py')):
            if py.name == '__init__.py':
                continue
            txt = py.read_text('utf-8', errors='replace')
            hits = re.findall(r'from \.([\w_]+_seq\d+_v\d+) import (.+)', txt)
            if not hits:
                continue
            existing = {f.stem for f in py.parent.glob('*.py')
                        if f.name != '__init__.py' and not f.name.startswith('.')}
            # build export map for siblings (include private names for internal wiring)
            sibling_exports = {}
            for stem in existing:
                for name in get_public_exports(py.parent / f'{stem}.py'):
                    sibling_exports.setdefault(name, stem)
                # also scan for ALL defined names including private
                try:
                    src2 = (py.parent / f'{stem}.py').read_text('utf-8', errors='replace')
                    for raw in re.findall(r'^(?:def|class) (\w+)|^(\w+)\s*=', src2, re.MULTILINE):
                        n = raw[0] or raw[1]
                        if n:
                            sibling_exports.setdefault(n, stem)
                except Exception:
                    pass
            new_txt = txt
            for old_mod, imports_str in hits:
                if (py.parent / f'{old_mod}.py').exists():
                    continue  # not broken
                names = [n.strip() for n in imports_str.split(',')]
                # find best matching sibling
                scores = {}
                for name in names:
                    if name in sibling_exports:
                        scores[sibling_exports[name]] = scores.get(sibling_exports[name], 0) + 1
                if scores:
                    best = max(scores, key=scores.get)
                    new_txt = new_txt.replace(
                        f'from .{old_mod} import {imports_str}',
                        f'from .{best} import {imports_str}'
                    )
            if new_txt != txt:
                py.write_text(new_txt, 'utf-8')
                fixed_internal += 1
                print(f'  FIXED internal: {py}')

    print(f'Fixed internal imports: {fixed_internal}')
    print(f'\nChecked: {checked} | Fixed: {fixed}')


if __name__ == '__main__':
    main()
