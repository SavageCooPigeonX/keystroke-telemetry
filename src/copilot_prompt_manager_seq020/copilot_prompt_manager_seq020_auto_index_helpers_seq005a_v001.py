"""copilot_prompt_manager_seq020_auto_index_helpers_seq005a_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

def _append_infra_index(lines: list[str], root: Path) -> None:
    # Scan client/, vscode-extension/ AND root-level .py files not already tracked
    infra_dirs = ['client', 'vscode-extension']
    infra_files: dict[str, list[str]] = {}
    for folder in infra_dirs:
        folder_path = root / folder
        if folder_path.is_dir():
            for py_file in sorted(folder_path.glob('*.py')):
                if py_file.name.startswith('__'):
                    continue
                infra_files.setdefault(folder, []).append(py_file.name)
    # Add root-level Python files (non-pigeon, non-dunder)
    root_py = sorted(
        p.name for p in root.glob('*.py')
        if not p.name.startswith('__') and '_seq' not in p.name
    )
    if root_py:
        infra_files['(root)'] = root_py
    if not infra_files:
        return
    lines.append('**Infrastructure (non-pigeon)**')
    lines.append('')
    lines.append('| File | Folder |')
    lines.append('|---|---|')
    for folder in sorted(infra_files):
        for name in infra_files[folder]:
            lines.append(f'| `{name}` | `{folder}` |')
    lines.append('')
