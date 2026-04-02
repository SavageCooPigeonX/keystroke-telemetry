"""copilot_prompt_manager_seq020_auto_index_builder_seq005b_v001.py — Token-compressed auto-index."""
from datetime import datetime, timezone
from pathlib import Path
import json
import re


def _load_keymap(root: Path) -> dict[str, str]:
    """Load {module_name: glyph} from dictionary.pgd."""
    pgd = root / 'dictionary.pgd'
    if pgd.exists():
        try:
            d = json.loads(pgd.read_text('utf-8'))
            mg = d.get('module_glyphs', {})
            return {name: glyph for glyph, name in mg.items()}
        except Exception:
            pass
    return {}


def _find_glyph(name: str, keymap: dict[str, str]) -> str:
    """Find glyph for a module, checking parent prefixes."""
    if name in keymap:
        return keymap[name]
    parts = name.split('_seq')
    if len(parts) > 1 and parts[0] in keymap:
        return keymap[parts[0]]
    for key in sorted(keymap, key=len, reverse=True):
        if name.startswith(key + '_') or name == key:
            return keymap[key]
    return ''


def _child_suffix(name: str, parent_name: str) -> str:
    """Extract child-specific name part, e.g. 'self_fix_seq013_scan_hardcoded' -> 'scan_hardcoded'."""
    m = re.match(rf'^{re.escape(parent_name)}_seq\d+_(.+)$', name)
    if m:
        return m.group(1)
    if name.startswith(parent_name + '_'):
        rest = name[len(parent_name) + 1:]
        return re.sub(r'^seq\d+_', '', rest) or name
    return name


def _build_auto_index_block(root: Path, registry: dict, processed: int) -> str:
    """Build token-compressed auto-index using Chinese keymap.

    Format:  glyph·seq desc tokens  (root modules)
             └ child_name(seq) ...  (collapsed children)
    """
    keymap = _load_keymap(root)
    items = _registry_items(registry)

    groups: dict[str, list[dict]] = {}
    seen: set[str] = set()
    for path, entry in items:
        name = entry.get('name', '')
        seq = entry.get('seq', 0)
        dedup_key = f"{name}_seq{seq:03d}"
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        folder = str(Path(path).parent).replace('\\', '/')
        if folder == '.':
            folder = '(root)'
        groups.setdefault(folder, []).append({
            'name': name, 'seq': seq,
            'desc': (entry.get('desc') or '').replace('_', ' ')[:40],
            'tokens': entry.get('tokens', 0),
            'glyph': _find_glyph(name, keymap),
        })

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    total = sum(len(v) for v in groups.values())
    lines = [
        '<!-- pigeon:auto-index -->',
        f'*{today} · {total} modules · {processed} touched*',
        '*Key: glyph·seq desc tokens | dictionary decodes glyphs*',
        '',
    ]

    # Identify child folders (compiled sub-packages)
    child_folders = set()
    parent_lookup: dict[str, str] = {}
    for folder in groups:
        parts = folder.replace('\\', '/').split('/')
        if len(parts) >= 2 and '_seq' in parts[-1]:
            child_folders.add(folder)
            m = re.match(r'^(\w+)_seq\d+', parts[-1])
            if m:
                parent_lookup[folder] = m.group(1)

    for folder in sorted(groups.keys()):
        folder_items = sorted(groups[folder], key=lambda x: (x['seq'], x['name']))
        if folder in child_folders:
            parent_name = parent_lookup.get(folder, '')
            g = _find_glyph(parent_name, keymap) if parent_name else ''
            total_tok = sum(i['tokens'] for i in folder_items)
            tok_s = f"{total_tok/1000:.1f}K" if total_tok >= 1000 else str(total_tok)
            children = ' '.join(
                f"{_child_suffix(i['name'], parent_name)}({i['seq']})"
                for i in folder_items
            )
            lines.append(f'  {g}└ {children} [{tok_s}]' if g else f'  └ {children} [{tok_s}]')
        else:
            child_count = sum(
                len(groups.get(cf, []))
                for cf in child_folders if cf.startswith(folder + '/')
            )
            lines.append(f'**{folder}** ({len(folder_items) + child_count})')
            for item in folder_items:
                g = item['glyph']
                desc = item['desc']
                if desc in ('auto extracted by pigeon compiler', 'pigeon extracted by compiler'):
                    desc = ''
                tok = item['tokens']
                tok_s = f"{tok/1000:.1f}K" if tok >= 1000 else str(tok)
                label = g or item['name'][:16]
                lines.append(f'{label}{item["seq"]} {desc} {tok_s}'.rstrip())
            lines.append('')

    _append_infra_index(lines, root)
    lines.append('<!-- /pigeon:auto-index -->')
    return '\n'.join(lines)
