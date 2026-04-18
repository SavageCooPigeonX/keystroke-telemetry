"""Seed plain-named .py files into the pigeon naming convention.

Assigns {stem}_seq001_v001 to each plain file, renames via git mv,
then rewrites all imports in the codebase so nothing breaks.

Usage:
    py _seed_pigeon_names.py            # dry run
    py _seed_pigeon_names.py --execute  # apply
"""
import re, sys, json, subprocess
from pathlib import Path

ROOT = Path('.')
EXECUTE = '--execute' in sys.argv

CODE_DIRS = ['src', 'pigeon_compiler', 'pigeon_brain', 'client']
PIGEON_RE = re.compile(r'(_seq\d{3,}|_s\d{3,}_v\d{3,})')
SKIP_DIRS = {'.git', '__pycache__', 'node_modules', 'dist', 'build', 'venv', '.venv'}

# Files that are externally referenced entry points — keep plain
SKIP_STEMS = {
    'thought_completer', 'git_plugin', 'cli', 'pigeon_limits',
    'pre_commit_audit', 'session_logger', 'os_hook', 'vscdb_poller',
    'master_test', '_resolve',
}


def _collect_plain():
    plain = []
    for d in CODE_DIRS:
        dp = ROOT / d
        if not dp.exists():
            continue
        for p in sorted(dp.rglob('*.py')):
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            if p.name.startswith('.') or p.stem.startswith('__') or p.stem.startswith('_'):
                continue
            if p.stem in SKIP_STEMS:
                continue
            if PIGEON_RE.search(p.stem):
                continue
            plain.append(p)
    return plain


def _make_new_stem(stem: str) -> str:
    return f'{stem}_seq001_v001'


def _build_import_map(plain_files):
    """Build old_module_path → new_module_path mapping for import rewriting."""
    mapping = {}
    for p in plain_files:
        old_stem = p.stem
        new_stem = _make_new_stem(old_stem)
        # Compute dotted module paths relative to root
        try:
            rel = p.relative_to(ROOT)
        except ValueError:
            continue
        parts = list(rel.with_suffix('').parts)
        old_mod = '.'.join(parts)
        new_parts = parts[:-1] + [new_stem]
        new_mod = '.'.join(new_parts)
        # Also map just the stem (for bare imports)
        mapping[old_stem] = new_stem
        if old_mod != old_stem:
            mapping[old_mod] = new_mod
    return mapping


def _rewrite_imports(import_map):
    # Longest first to avoid partial replacements
    sorted_pairs = sorted(import_map.items(), key=lambda x: len(x[0]), reverse=True)
    changed = 0
    for py in sorted(ROOT.rglob('*.py')):
        rel = py.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        try:
            text = py.read_text('utf-8', errors='ignore')
        except Exception:
            continue
        new_text = text
        for old, new in sorted_pairs:
            if old in new_text:
                new_text = new_text.replace(old, new)
        if new_text != text:
            changed += 1
            if EXECUTE:
                py.write_text(new_text, 'utf-8')
    return changed


def main():
    plain = _collect_plain()
    print(f'Found {len(plain)} plain-named files\n')

    if not plain:
        print('Nothing to do.')
        return

    import_map = _build_import_map(plain)

    renames = []
    for p in plain:
        new_name = _make_new_stem(p.stem) + '.py'
        new_path = p.parent / new_name
        renames.append((p, new_path))
        marker = '' if p.exists() else ' [MISSING?]'
        print(f'  {p.relative_to(ROOT)} → {new_path.name}{marker}')

    print(f'\nImport rewrites: {len(import_map)} entries')

    if not EXECUTE:
        print('\n[DRY RUN] Pass --execute to apply.')
        return

    errors = []
    renamed = 0
    for old_p, new_p in renames:
        if new_p.exists():
            print(f'  SKIP (exists): {new_p.relative_to(ROOT)}')
            continue
        try:
            result = subprocess.run(
                ['git', 'mv', str(old_p), str(new_p)],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                # Fall back to plain rename if git mv fails
                old_p.rename(new_p)
            renamed += 1
        except Exception as e:
            errors.append(f'{old_p}: {e}')

    print(f'\nRenamed: {renamed} files')

    changed = _rewrite_imports(import_map)
    print(f'Import files rewritten: {changed}')

    # Save log
    log = {'renames': [(str(a), str(b)) for a, b in renames], 'import_map': import_map}
    log_path = ROOT / 'logs' / 'seed_pigeon_log.json'
    log_path.parent.mkdir(exist_ok=True)
    log_path.write_text(json.dumps(log, indent=2, ensure_ascii=False), 'utf-8')
    print(f'Log: {log_path.relative_to(ROOT)}')

    if errors:
        print(f'\nErrors ({len(errors)}):')
        for e in errors[:20]:
            print(' ', e)


if __name__ == '__main__':
    main()
