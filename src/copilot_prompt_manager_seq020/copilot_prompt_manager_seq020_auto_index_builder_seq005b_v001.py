"""copilot_prompt_manager_seq020_auto_index_builder_seq005b_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
import re

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
