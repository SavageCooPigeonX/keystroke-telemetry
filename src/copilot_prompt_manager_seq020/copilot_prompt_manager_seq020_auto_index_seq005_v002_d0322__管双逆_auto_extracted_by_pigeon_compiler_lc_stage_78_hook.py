"""copilot_prompt_manager_seq020_auto_index_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v002 | 67 lines | ~665 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: stage_78_hook
# LAST:   2026-03-22 @ 276af14
# SESSIONS: 1
# ──────────────────────────────────────────────
from datetime import datetime, timezone
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


def _build_auto_index_block(root: Path, registry: dict, processed: int) -> str:
    groups: dict[str, list] = {}
    items = _registry_items(registry)
    for path, entry in items:
        folder = str(Path(path).parent).replace('\\', '/')
        groups.setdefault(folder, []).append({
            'name': entry.get('name', ''),
            'seq': entry.get('seq', 0),
            'desc': (entry.get('desc') or '').replace('_', ' ')[:52],
            'tokens': entry.get('tokens', 0),
        })

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    lines = [
        '<!-- pigeon:auto-index -->',
        f'*Auto-updated {today} - {len(items)} modules tracked | {processed} touched this commit*',
        '',
    ]
    for folder in sorted(groups.keys()):
        items = sorted(groups[folder], key=lambda item: (item['seq'], item['name']))
        lines.append(f'**{folder}/** - {len(items)} module(s)')
        lines.append('')
        lines.append('| Search pattern | Desc | Tokens |')
        lines.append('|---|---|---:|')
        for item in items:
            pattern = f'`{item["name"]}_seq{item["seq"]:03d}*`'
            lines.append(f'| {pattern} | {item["desc"]} | ~{item["tokens"]:,} |')
        lines.append('')

    _append_infra_index(lines, root)
    lines.append('<!-- /pigeon:auto-index -->')
    return '\n'.join(lines)
