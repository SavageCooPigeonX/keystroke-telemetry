"""manifest_builder_seq007_build_all_manifests_seq031_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import ast
import re

def build_all_manifests(root: Path, dry_run: bool = False) -> list[dict]:
    """Build MANIFEST.md for every folder that has .py files.

    Returns list of {folder, files, wrote} dicts.
    """
    root = Path(root)
    results = []
    seen = set()
    for py in sorted(root.rglob('*.py')):
        if _should_skip(py, root):
            continue
        folder = py.parent
        if folder in seen:
            continue
        seen.add(folder)
        content = build_manifest(folder, root)
        if not content:
            continue
        files_in = content.count('\n|') - 1  # minus header
        result = {'folder': str(folder.relative_to(root)).replace('\\', '/'),
                  'files': max(files_in, 0)}
        if not dry_run:
            (folder / 'MANIFEST.md').write_text(content, encoding='utf-8')
            result['wrote'] = True
        else:
            result['wrote'] = False
        results.append(result)
    # Sync project structure into MASTER_MANIFEST.md
    if not dry_run:
        sync_master_structure(root, results)
    return results
