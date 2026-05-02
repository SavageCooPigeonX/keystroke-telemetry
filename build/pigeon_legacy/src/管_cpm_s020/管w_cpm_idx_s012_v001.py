"""管w_cpm_idx_s012_v001.py — auto-index builder for copilot prompt manager.

Builds the <!-- pigeon:auto-index --> block from pigeon_registry.json.
Self-contained: all required helpers duplicated here to avoid circular imports.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 012 | VER: v001 | 252 lines | ~2,662 tokens
# DESC:   auto_index_builder_for_copilot
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

# ── data tables ─────────────────────────────────────────────────────────────

_INTENT_LABELS = {
    'FX': 'fix', 'RN': 'rename', 'RF': 'refactor', 'SP': 'split',
    'TL': 'telemetry', 'CP': 'compress', 'VR': 'verify', 'FT': 'feature',
    'CL': 'cleanup', 'OT': 'other',
}
_BUG_LEGEND = {
    'hi': 'hardcoded_import', 'de': 'dead_export', 'dd': 'duplicate_docstring',
    'hc': 'high_coupling', 'oc': 'over_hard_cap', 'qn': 'query_noise',
}
_BUG_KEY_ORDER = ('oc', 'hi', 'hc', 'de', 'dd', 'qn')
_INTENT_CODE_RULES: list[tuple[tuple[str, ...], str]] = [
    (('fix', 'bug', 'repair', 'heal', 'restore', 'wrong', 'broken'), 'FX'),
    (('rename', 'nametag'), 'RN'),
    (('refactor', 'restructure'), 'RF'),
    (('split', 'decompose', 'compile'), 'SP'),
    (('telemetry', 'prompt', 'operator', 'journal', 'context', 'unsaid', 'voice', 'engagement'), 'TL'),
    (('compress', 'glyph', 'dictionary', 'token'), 'CP'),
    (('verify', 'test', 'audit', 'validate', 'check'), 'VR'),
    (('feature', 'add', 'implement', 'build', 'create'), 'FT'),
    (('cleanup', 'chore', 'docs', 'update'), 'CL'),
]

# ── file/dict loaders ────────────────────────────────────────────────────────

def _load_keymap(root: Path) -> dict[str, str]:
    pgd = root / 'dictionary.pgd'
    if pgd.exists():
        try:
            d = json.loads(pgd.read_text('utf-8'))
            return {name: glyph for glyph, name in d.get('module_glyphs', {}).items()}
        except Exception:
            pass
    return {}


def _load_confidence(root: Path) -> dict[str, str]:
    pgd = root / 'dictionary.pgd'
    if pgd.exists():
        try:
            return json.loads(pgd.read_text('utf-8')).get('confidence', {})
        except Exception:
            pass
    return {}


def _load_dict_extras(root: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Load 2-letter codes and intent glyphs from dictionary.pgd."""
    pgd = root / 'dictionary.pgd'
    if pgd.exists():
        try:
            d = json.loads(pgd.read_text('utf-8'))
            mg = d.get('module_glyphs', {})
            return {g: n for g, n in mg.items() if g.isascii()}, d.get('intent_glyphs', {})
        except Exception:
            pass
    return {}, {}


def _registry_items(registry: dict | None) -> list[tuple[str, dict]]:
    if not registry:
        return []
    if isinstance(registry, dict) and isinstance(registry.get('files'), list):
        return [(e.get('path', ''), e) for e in registry['files'] if isinstance(e, dict)]
    if isinstance(registry, dict):
        return [(p, e) for p, e in registry.items() if isinstance(e, dict)]
    return []

# ── name / glyph helpers ─────────────────────────────────────────────────────

def _find_glyph(name: str, keymap: dict[str, str]) -> str:
    if name in keymap: return keymap[name]
    parts = name.split('_seq')
    if len(parts) > 1 and parts[0] in keymap: return keymap[parts[0]]
    for key in sorted(keymap, key=len, reverse=True):
        if name.startswith(key + '_') or name == key: return keymap[key]
    return ''


def _child_suffix(name: str, parent_name: str) -> str:
    m = re.match(rf'^{re.escape(parent_name)}_seq\d+_(.+)$', name)
    if m: return m.group(1)
    if name.startswith(parent_name + '_'):
        return re.sub(r'^seq\d+_', '', name[len(parent_name) + 1:]) or name
    return name

# ── intent / bug formatters ──────────────────────────────────────────────────

def _intent_code(intent: str) -> str:
    text = (intent or '').lower()
    for needles, code in _INTENT_CODE_RULES:
        if any(needle in text for needle in needles): return code
    return 'OT' if not text else text[:2].upper()


def _intent_label(intent: str) -> str:
    return '_'.join([w for w in (intent or '').split('_') if w][:2]) or 'other'


def _build_intent_legend(items_raw: list[tuple[str, dict]]) -> dict[str, str]:
    legend = dict(_INTENT_LABELS)
    for _, entry in items_raw:
        code = entry.get('intent_code') or _intent_code(entry.get('intent', ''))
        if code and code not in legend:
            legend[code] = _intent_label(entry.get('intent', ''))
    return legend


def _fmt_bug_keys(keys: list[str]) -> str:
    keys = [k for k in keys if k]
    if not keys: return ''
    return '+'.join(keys) if len(keys) <= 3 else f'{"+".join(keys[:3])}+{len(keys) - 3}'

# ── infra section ────────────────────────────────────────────────────────────

def _append_infra_index(lines: list[str], root: Path) -> None:
    infra_files: dict[str, list[str]] = {}
    for folder in ['client', 'vscode-extension']:
        fp = root / folder
        if fp.is_dir():
            for py in sorted(fp.glob('*.py')):
                if not py.name.startswith('__'):
                    infra_files.setdefault(folder, []).append(py.stem)
    root_py = sorted(p.stem for p in root.glob('*.py')
                     if not p.name.startswith('__') and '_seq' not in p.name)
    if root_py:
        infra_files['(root)'] = root_py
    if not infra_files:
        return
    lines.append('**Infra**')
    for folder in sorted(infra_files):
        lines.append(f'{folder}: {", ".join(infra_files[folder])}')

# ── main builder ─────────────────────────────────────────────────────────────

def _build_auto_index_block(root: Path, registry: dict, processed: int) -> str:
    keymap = _load_keymap(root)
    confidence = _load_confidence(root)
    two_letter, _intents = _load_dict_extras(root)
    items_raw = _registry_items(registry)
    intent_legend = _build_intent_legend(items_raw)

    dossier_conf, focus_mods = 0.0, []
    dossier_path = root / 'logs' / 'active_dossier.json'
    if dossier_path.exists():
        try:
            d = json.loads(dossier_path.read_text('utf-8', errors='ignore'))
            ts = d.get('ts', '')
            if ts and (datetime.now(timezone.utc) - datetime.fromisoformat(ts)).total_seconds() <= 300:
                dossier_conf = d.get('confidence', 0.0)
                focus_mods = d.get('focus_modules', [])
        except Exception:
            pass
    slim_index = dossier_conf >= 0.7 and focus_mods
    focus_stems = {m.lower().split('_seq')[0].split('_s0')[0].split('_s1')[0] for m in focus_mods}

    groups: dict[str, list[dict]] = {}
    seen: set[str] = set()
    for path, entry in items_raw:
        name = entry.get('name', '')
        seq = entry.get('seq', 0)
        dedup_key = f"{name}_seq{seq:03d}"
        if dedup_key in seen: continue
        seen.add(dedup_key)
        if slim_index:
            name_stem = name.lower().split('_seq')[0].split('_s0')[0].split('_s1')[0]
            if name_stem not in focus_stems and not entry.get('bug_keys'): continue
        folder = str(Path(path).parent).replace('\\', '/')
        if folder == '.': folder = '(root)'
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
    states = list(confidence.values())
    n = len(states) or 1
    conf_s = f'✓{states.count("✓")*100//n}% ~{states.count("~")*100//n}% !{states.count("!")*100//n}%'

    lines = [
        '<!-- pigeon:auto-index -->',
        f'*{today} · {total} modules · {processed} touched · {conf_s}*',
    ]
    if slim_index:
        lines.append(f'*🎯 DOSSIER ROUTED — showing {total} focus+bugged modules '
                     f'(conf={dossier_conf:.2f}, focus: {", ".join(focus_mods[:3])})*')
    lines.append('*Format: glyph=name seq tokens·state·intent·bugs |last change*')
    if two_letter:
        lines.append('*' + ' '.join(f'{g}={nn}' for g, nn in sorted(two_letter.items())) + '*')
    lines.append('*Intent: ' + ' '.join(f'{c}={lb}' for c, lb in intent_legend.items()) + '*')
    lines.append('*Bugs: ' + ' '.join(f'{c}={lb}' for c, lb in _BUG_LEGEND.items()) + '*')
    lines.append('')

    child_folders: set[str] = set()
    parent_lookup: dict[str, str] = {}
    for folder in groups:
        parts = folder.replace('\\', '/').split('/')
        if len(parts) >= 2 and '_seq' in parts[-1]:
            child_folders.add(folder)
            m = re.match(r'^(\w+)_seq\d+', parts[-1])
            if m: parent_lookup[folder] = m.group(1)

    for folder in sorted(groups.keys()):
        items = sorted(groups[folder], key=lambda x: (x['seq'], x['name']))
        if folder in child_folders:
            parent_name = parent_lookup.get(folder, '')
            g = _find_glyph(parent_name, keymap) if parent_name else ''
            total_tok = sum(i['tokens'] for i in items)
            tok_s = f"{total_tok/1000:.1f}K" if total_tok >= 1000 else str(total_tok)
            children = ' '.join(f"{_child_suffix(i['name'], parent_name)}({i['seq']})" for i in items)
            lines.append(f'  {g}└ {children} [{tok_s}]' if g else f'  └ {children} [{tok_s}]')
        else:
            child_count = sum(len(groups.get(cf, [])) for cf in child_folders if cf.startswith(folder + '/'))
            lines.append(f'**{folder}** ({len(items) + child_count})')
            for item in items:
                g = item['glyph']
                state = confidence.get(item['name'], '')
                tok = item['tokens']
                tok_s = f"{tok/1000:.1f}K" if tok >= 1000 else str(tok)
                bug_code = _fmt_bug_keys(item.get('bug_keys', []))
                lc_suffix = f' |{item["last_change"]}' if item.get('last_change') else ''
                meta = [f'{tok_s}{state}' if state else tok_s]
                if item.get('intent_code'): meta.append(item['intent_code'])
                if bug_code: meta.append(bug_code)
                meta_s = '·'.join(meta)
                if g:
                    lines.append(f'{g}={item["name"]} {item["seq"]} {meta_s}{lc_suffix}')
                else:
                    lines.append(f'{item["name"]} {item["seq"]} {meta_s}{lc_suffix}')
            lines.append('')

    _append_infra_index(lines, root)
    lines.append('<!-- /pigeon:auto-index -->')
    return '\n'.join(lines)
