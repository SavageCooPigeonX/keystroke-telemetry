"""管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_auto_index_decomposed_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
import re

def _build_auto_index_block(root: Path, registry: dict, processed: int) -> str:
    keymap = _load_keymap(root)
    confidence = _load_confidence(root)
    two_letter, intents = _load_dict_extras(root)
    items_raw = _registry_items(registry)
    intent_legend = _build_intent_legend(items_raw)

    groups: dict[str, list[dict]] = {}
    seen: set[str] = set()
    for path, entry in items_raw:
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
            'tokens': entry.get('tokens', 0),
            'glyph': _find_glyph(name, keymap),
            'intent_code': entry.get('intent_code') or _intent_code(entry.get('intent', '')),
            'bug_keys': entry.get('bug_keys', []),
            'last_change': entry.get('last_change', ''),
        })

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    total = sum(len(v) for v in groups.values())

    # Confidence summary
    states = list(confidence.values())
    n = len(states) or 1
    conf = f'✓{states.count("✓")*100//n}% ~{states.count("~")*100//n}% !{states.count("!")*100//n}%'

    lines = [
        '<!-- pigeon:auto-index -->',
        f'*{today} · {total} modules · {processed} touched · {conf}*',
        f'*Format: glyph=name seq tokens·state·intent·bugs |last change*',
    ]

    # 2-letter codes legend (for modules without Chinese glyphs)
    if two_letter:
        codes = ' '.join(f'{g}={n}' for g, n in sorted(two_letter.items()))
        lines.append(f'*{codes}*')
    lines.append('*Intent: ' + ' '.join(f'{code}={label}' for code, label in intent_legend.items()) + '*')
    lines.append('*Bugs: ' + ' '.join(f'{code}={label}' for code, label in _BUG_LEGEND.items()) + '*')
    lines.append('')

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
                name = item['name']
                state = confidence.get(name, '')
                tok = item['tokens']
                tok_s = f"{tok/1000:.1f}K" if tok >= 1000 else str(tok)
                intent_code = item.get('intent_code', '')
                bug_code = _fmt_bug_keys(item.get('bug_keys', []))
                lc = item.get('last_change', '')
                lc_suffix = f' |{lc}' if lc else ''
                meta = [f'{tok_s}{state}' if state else tok_s]
                if intent_code:
                    meta.append(intent_code)
                if bug_code:
                    meta.append(bug_code)
                meta_s = '·'.join(meta)
                if g:
                    lines.append(f'{g}={name} {item["seq"]} {meta_s}{lc_suffix}')
                else:
                    lines.append(f'{name} {item["seq"]} {meta_s}{lc_suffix}')
            lines.append('')

    _append_infra_index(lines, root)
    lines.append('<!-- /pigeon:auto-index -->')
    return '\n'.join(lines)
