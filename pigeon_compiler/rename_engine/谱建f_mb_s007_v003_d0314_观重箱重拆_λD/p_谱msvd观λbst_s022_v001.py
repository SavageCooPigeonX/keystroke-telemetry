"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_build_structure_tree_seq022_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 022 | VER: v001 | 76 lines | ~714 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
from pigeon_compiler.pigeon_limits import PIGEON_MAX, PIGEON_RECOMMENDED, is_excluded
import json
import re

def _build_structure_tree(root: Path) -> str:
    """Generate a text tree of the project folder structure with stats."""
    lines = ['LinkRouter.AI/\n']

    # Root files
    root_files = sorted(f for f in root.iterdir()
                        if f.is_file() and f.suffix in ('.py', '.md', '.txt', '.json', '.toml'))
    for f in root_files:
        if f.name.startswith('.'):
            continue
        lines.append(f'+-- {f.name}\n')

    lines.append('|\n')

    # Folders (1 level deep with file counts)
    folders = sorted(d for d in root.iterdir()
                     if d.is_dir() and d.name not in SKIP_DIRS
                     and not d.name.startswith('.'))
    for folder in folders:
        py_files = list(folder.rglob('*.py'))
        py_files = [p for p in py_files if '__pycache__' not in str(p)]
        if not py_files and not (folder / '__init__.py').exists():
            # Non-Python folder (static, templates, etc.)
            all_files = list(folder.rglob('*'))
            all_files = [f for f in all_files if f.is_file()]
            if all_files:
                lines.append(f'+-- /{folder.name:<35s} ({len(all_files)} files)\n')
            continue

        # Count compliance
        ok = warn = over = 0
        for py in py_files:
            if py.name == '__init__.py':
                continue
            try:
                lc = len(py.read_text(encoding='utf-8', errors='ignore').splitlines())
            except Exception:
                continue
            if lc <= PIGEON_RECOMMENDED:
                ok += 1
            elif lc <= MAX_COMPLIANT:
                warn += 1
            else:
                over += 1
        total = ok + warn + over
        if total == 0:
            lines.append(f'+-- /{folder.name:<35s} (package)\n')
            continue

        # Subfolder count
        subdirs = [d for d in folder.iterdir() if d.is_dir()
                   and d.name not in SKIP_DIRS and not d.name.startswith('__')]
        sub_str = f', {len(subdirs)} sub' if subdirs else ''
        pct = 100 * (ok + warn) / total if total else 0
        lines.append(
            f'+-- /{folder.name:<35s} '
            f'{total} files{sub_str} | '
            f'{pct:.0f}% compliant\n'
        )

        # Show subfolders (1 level)
        for sub in sorted(subdirs):
            sub_py = [p for p in sub.rglob('*.py')
                      if '__pycache__' not in str(p) and p.name != '__init__.py']
            if sub_py:
                lines.append(f'|   +-- /{sub.name:<31s} ({len(sub_py)} files)\n')

        lines.append('|\n')

    return ''.join(lines)
