"""Copilot prompt manager — audits and manages all injected prompt blocks."""

# ── pigeon ────────────────────────────────────
# SEQ: 020 | VER: v003 | 781 lines | ~7,179 tokens
# DESC:   audits_and_manages_all_injected
# INTENT: verify_filename_mutation
# LAST:   2026-04-02 @ 4eb4c79
# SESSIONS: 1
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   2026-04-02T19:57:36.8206812Z
# EDIT_HASH: auto
# EDIT_WHY:  inject bug voices layer
# EDIT_STATE: harvested
# ── /pulse ──

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

COPILOT_PATH = '.github/copilot-instructions.md'
SNAPSHOT_PATH = 'logs/prompt_telemetry_latest.json'
AUDIT_PATH = 'logs/copilot_prompt_audit.json'

PROMPT_BLOCK_START = '<!-- pigeon:prompt-telemetry -->'
PROMPT_BLOCK_END = '<!-- /pigeon:prompt-telemetry -->'

BLOCK_MARKERS = {
    'task_context': ('<!-- pigeon:task-context -->', '<!-- /pigeon:task-context -->'),
    'task_queue': ('<!-- pigeon:task-queue -->', '<!-- /pigeon:task-queue -->'),
    'operator_state': ('<!-- pigeon:operator-state -->', '<!-- /pigeon:operator-state -->'),
    'prompt_telemetry': (PROMPT_BLOCK_START, PROMPT_BLOCK_END),
    'auto_index': ('<!-- pigeon:auto-index -->', '<!-- /pigeon:auto-index -->'),
    'bug_voices': ('<!-- pigeon:bug-voices -->', '<!-- /pigeon:bug-voices -->'),
}

_STATE_HINTS: dict[str, str] = {
    'frustrated': 'concise answers, 2-3 options max, bullets, lead with solution',
    'hesitant': 'warm tone, anticipate intent, ask one follow-up question',
    'flow': 'match energy - full technical depth, no hand-holding',
    'focused': 'thorough and structured, match effort level',
    'restructuring': 'precise, use headers/numbered lists to mirror their effort',
    'abandoned': 'welcoming, direct - they re-approached after backing off',
    'neutral': 'standard response style',
}


def _block_pattern(start: str, end: str) -> re.Pattern[str]:
    return re.compile(
        rf'(?ms)^\s*{re.escape(start)}\s*$\n.*?^\s*{re.escape(end)}\s*$',
    )


def _extract_block(text: str, start: str, end: str) -> str | None:
    match = _block_pattern(start, end).search(text)
    return match.group(0) if match else None


def _count_blocks(text: str, start: str, end: str) -> int:
    return len(_block_pattern(start, end).findall(text))


def _replace_or_insert_after_line(text: str, anchor: str, block: str) -> str:
    anchor_pattern = re.compile(rf'(?m)^\s*{re.escape(anchor)}\s*$')
    match = anchor_pattern.search(text)
    if not match:
        return text.rstrip() + '\n\n' + block + '\n'
    insert_at = match.end()
    return text[:insert_at] + '\n\n' + block + text[insert_at:]


def _load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None


def _latest_runtime_module(root: Path, pattern: str) -> Path | None:
    matches = sorted(root.glob(pattern))
    return matches[-1] if matches else None


def _run_refresher(root: Path, relative_path: str | None, function_name: str) -> bool:
    try:
        import importlib.util

        if relative_path is None:
            return False
        mod_path = root / relative_path
        if not mod_path.exists():
            latest = _latest_runtime_module(root, relative_path)
            if latest is None:
                return False
            mod_path = latest
        spec = importlib.util.spec_from_file_location(f'_prompt_refresh_{function_name}', mod_path)
        if spec is None or spec.loader is None:
            return False
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        func = getattr(mod, function_name, None)
        if not callable(func):
            return False
        return bool(func(root))
    except Exception:
        return False


def _render_prompt_block(snapshot: dict) -> str:
    return (
        f'{PROMPT_BLOCK_START}\n'
        '## Live Prompt Telemetry\n\n'
        f'*Auto-updated per prompt · source: `{SNAPSHOT_PATH}`*\n\n'
        'Use this block as the highest-freshness prompt-level telemetry. '
        'When it conflicts with older commit-time context, prefer this block.\n\n'
        '```json\n'
        f'{json.dumps(snapshot, ensure_ascii=False, indent=2)}\n'
        '```\n\n'
        f'{PROMPT_BLOCK_END}'
    )


def _append_infra_index(lines: list[str], root: Path) -> None:
    infra_dirs = ['client', 'vscode-extension']
    infra_files: dict[str, list[str]] = {}
    for folder in infra_dirs:
        folder_path = root / folder
        if folder_path.is_dir():
            for py_file in sorted(folder_path.glob('*.py')):
                if py_file.name.startswith('__'):
                    continue
                infra_files.setdefault(folder, []).append(py_file.stem)
    root_py = sorted(
        p.stem for p in root.glob('*.py')
        if not p.name.startswith('__') and '_seq' not in p.name
    )
    if root_py:
        infra_files['(root)'] = root_py
    if not infra_files:
        return
    lines.append('**Infra**')
    for folder in sorted(infra_files):
        lines.append(f'{folder}: {", ".join(infra_files[folder])}')


def _registry_items(registry: dict | None) -> list[tuple[str, dict]]:
    if not registry:
        return []
    if isinstance(registry, dict) and isinstance(registry.get('files'), list):
        items: list[tuple[str, dict]] = []
        for entry in registry['files']:
            if isinstance(entry, dict):
                items.append((entry.get('path', ''), entry))
        return items
    if isinstance(registry, dict):
        items = []
        for path, entry in registry.items():
            if isinstance(entry, dict):
                items.append((path, entry))
        return items
    return []


def _load_keymap(root: Path) -> dict[str, str]:
    pgd = root / 'dictionary.pgd'
    if pgd.exists():
        try:
            d = json.loads(pgd.read_text('utf-8'))
            mg = d.get('module_glyphs', {})
            return {name: glyph for glyph, name in mg.items()}
        except Exception:
            pass
    return {}


def _load_confidence(root: Path) -> dict[str, str]:
    pgd = root / 'dictionary.pgd'
    if pgd.exists():
        try:
            d = json.loads(pgd.read_text('utf-8'))
            return d.get('confidence', {})
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
            ig = d.get('intent_glyphs', {})
            two_letter = {g: n for g, n in mg.items() if g.isascii()}
            return two_letter, ig
        except Exception:
            pass
    return {}, {}


_INTENT_LABELS = {
    'FX': 'fix',
    'RN': 'rename',
    'RF': 'refactor',
    'SP': 'split',
    'TL': 'telemetry',
    'CP': 'compress',
    'VR': 'verify',
    'FT': 'feature',
    'CL': 'cleanup',
    'OT': 'other',
}

_BUG_LEGEND = {
    'hi': 'hardcoded_import',
    'de': 'dead_export',
    'dd': 'duplicate_docstring',
    'hc': 'high_coupling',
    'oc': 'over_hard_cap',
    'qn': 'query_noise',
}

_BUG_KEY_ORDER = ('oc', 'hi', 'hc', 'de', 'dd', 'qn')

_BUG_PERSONAS = {
    'hi': ('Hardcode Gremlin', 'I weld imports to exact paths and squeal when rename day comes.'),
    'de': ('Dead Export Shade', 'I leave dead functions standing so everyone thinks they still matter.'),
    'dd': ('Mirror Imp', 'I duplicate the same explanation until nobody remembers which copy was first.'),
    'hc': ('Coupling Leech', 'I braid modules together until one cut hurts five files.'),
    'oc': ('Overcap Maw', 'I keep swelling this file past the hard cap. Split me before I eat context.'),
    'qn': ('Noise Imp', 'I fog the query stream until the real intent has to fight to stay visible.'),
}

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


def _intent_code(intent: str) -> str:
    text = (intent or '').lower()
    for needles, code in _INTENT_CODE_RULES:
        if any(needle in text for needle in needles):
            return code
    if not text:
        return 'OT'
    return text[:2].upper()


def _intent_label(intent: str) -> str:
    words = [w for w in (intent or '').split('_') if w][:2]
    return '_'.join(words) or 'other'


def _build_intent_legend(items_raw: list[tuple[str, dict]]) -> dict[str, str]:
    legend = dict(_INTENT_LABELS)
    for _, entry in items_raw:
        code = entry.get('intent_code') or _intent_code(entry.get('intent', ''))
        if code and code not in legend:
            legend[code] = _intent_label(entry.get('intent', ''))
    return legend


def _fmt_bug_keys(keys: list[str]) -> str:
    keys = [k for k in keys if k]
    if not keys:
        return ''
    if len(keys) <= 3:
        return '+'.join(keys)
    return f'{"+".join(keys[:3])}+{len(keys) - 3}'


def _primary_bug(entry: dict) -> str:
    keys = [key for key in entry.get('bug_keys', []) if key]
    counts = entry.get('bug_counts', {}) or {}
    if not keys:
        return ''
    order = {key: idx for idx, key in enumerate(_BUG_KEY_ORDER)}
    return max(
        keys,
        key=lambda key: (int(counts.get(key, 0)), -order.get(key, len(order)), key),
    )


def _bug_voice_score(entry: dict) -> int:
    counts = entry.get('bug_counts', {}) or {}
    active = [key for key in entry.get('bug_keys', []) if key]
    return len(active) * 10 + sum(int(counts.get(key, 0)) for key in active)


def _build_bug_voices_block(root: Path, registry: dict | None) -> str:
    if registry is None:
        registry = _load_json(root / 'pigeon_registry.json')
    items = [
        (path, entry)
        for path, entry in _registry_items(registry)
        if entry.get('bug_keys')
    ]
    lines = [
        '<!-- pigeon:bug-voices -->',
        '## Bug Voices',
        '',
        '*Persistent bug demons minted from registry scars - active filename bugs first.*',
        '',
    ]
    if not items:
        lines.append('- No active bug demons. The trapdoors are quiet for now.')
        lines.append('<!-- /pigeon:bug-voices -->')
        return '\n'.join(lines)

    items.sort(key=lambda item: (-_bug_voice_score(item[1]), item[1].get('name', '')))
    for _, entry in items[:5]:
        key = _primary_bug(entry)
        persona_name, voice = _BUG_PERSONAS.get(key, ('Bug Imp', 'I keep coming back.'))
        entity = (entry.get('bug_entities') or {}).get(key) or persona_name
        recur = int((entry.get('bug_counts') or {}).get(key, 1) or 1)
        others = [bug for bug in entry.get('bug_keys', []) if bug != key]
        others_s = f' other={"+".join(others)}' if others else ''
        mark = entry.get('last_bug_mark', 'unmarked')
        last_change = entry.get('last_change', '')
        last_s = f' last={last_change}' if last_change else ''
        lines.append(
            f'- `{entry.get("name", "?")}` {mark} · {key} `{entity}` x{recur}{others_s}: "{voice}"{last_s}'
        )

    lines.append('<!-- /pigeon:bug-voices -->')
    return '\n'.join(lines)


def _find_glyph(name: str, keymap: dict[str, str]) -> str:
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
    m = re.match(rf'^{re.escape(parent_name)}_seq\d+_(.+)$', name)
    if m:
        return m.group(1)
    if name.startswith(parent_name + '_'):
        rest = name[len(parent_name) + 1:]
        return re.sub(r'^seq\d+_', '', rest) or name
    return name


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


def _parse_operator_profile(root: Path) -> dict | None:
    prof_path = root / 'operator_profile.md'
    if not prof_path.exists():
        return None
    try:
        text = prof_path.read_text(encoding='utf-8')
    except Exception:
        return None

    def _re(pattern: str, default: str) -> str:
        match = re.search(pattern, text)
        return match.group(1) if match else default

    return {
        'messages': int(_re(r'(\d+) messages ingested', '0') or '0'),
        'dominant': _re(r'\*\*Dominant state:\s*(\w+)\*\*', 'neutral'),
        'submit_rate': int(_re(r'\*\*Submit rate:.*?\((\d+)%\)\*\*', '0') or '0'),
        'avg_wpm': float(_re(r'\|\s*WPM\s*\|[^|]+\|[^|]+\|\s*([\d.]+)\s*\|', '0') or '0'),
        'avg_del': float(_re(r'\|\s*Deletion\s*%\s*\|[^|]+\|[^|]+\|\s*([\d.]+)%', '0') or '0'),
        'avg_hes': float(_re(r'\|\s*Hesitation\s*\|[^|]+\|[^|]+\|\s*([\d.]+)\s*\|', '0') or '0'),
        'active_hours': _re(r'\*\*Active hours:\*\*\s*(.+)', '').strip(),
    }


def _load_coaching_prose(root: Path, max_age_s: float = 7200.0) -> str | None:
    """Load coaching prose from operator_coaching.md if file is < max_age_s old."""
    coaching_path = root / 'operator_coaching.md'
    if not coaching_path.exists():
        return None
    try:
        import time as _time
        age_s = _time.time() - coaching_path.stat().st_mtime
        if age_s > max_age_s:
            return None  # stale — don't inject outdated coaching
        text = coaching_path.read_text(encoding='utf-8')
        match = re.search(r'<!-- coaching:count=\d+ -->\n.*?\n(.*?)<!-- /coaching -->', text, re.DOTALL)
        if match:
            return match.group(1).strip()
    except Exception:
        return None
    return None


def _build_operator_state_block(root: Path) -> str | None:
    profile = _parse_operator_profile(root)
    if not profile or profile['messages'] == 0:
        return None

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    dominant = profile['dominant']
    coaching_prose = _load_coaching_prose(root)
    if coaching_prose:
        lines = [
            '<!-- pigeon:operator-state -->',
            '## Live Operator State',
            '',
            f'*Auto-updated {today} - {profile["messages"]} message(s) - LLM-synthesized*',
            '',
            (f'**Dominant: `{dominant}`** '
             f'| Submit: {profile["submit_rate"]}% '
             f'| WPM: {profile["avg_wpm"]:.1f} '
             f'| Del: {profile["avg_del"]:.1f}% '
             f'| Hes: {profile["avg_hes"]:.3f}'),
            '',
            coaching_prose,
            '',
            '<!-- /pigeon:operator-state -->',
        ]
        return '\n'.join(lines)

    hint = _STATE_HINTS.get(dominant, _STATE_HINTS['neutral'])
    lines = [
        '<!-- pigeon:operator-state -->',
        '## Live Operator State',
        '',
        f'*Auto-updated {today} - {profile["messages"]} message(s) in profile*',
        '',
        (f'**Dominant: `{dominant}`** '
         f'| Submit: {profile["submit_rate"]}% '
         f'| WPM: {profile["avg_wpm"]:.1f} '
         f'| Del: {profile["avg_del"]:.1f}% '
         f'| Hes: {profile["avg_hes"]:.3f}'),
        '',
        '**Behavioral tunes for this session:**',
        f'- **{dominant}** -> {hint}',
    ]
    if profile['avg_wpm'] < 45:
        lines.append('- WPM < 45 -> prefer bullets and code blocks over dense prose')
    if profile['avg_del'] > 30:
        lines.append('- Deletion ratio > 30% -> high rethinking; consider asking "what specifically do you need?"')
    if profile['submit_rate'] < 60:
        lines.append(
            f'- Submit rate {profile["submit_rate"]}% -> messages often abandoned; check if previous answer landed before going deep'
        )
    if profile['avg_hes'] > 0.4:
        lines.append('- Hesitation > 0.4 -> uncertain operator; proactively offer alternatives or examples')
    if profile['active_hours']:
        lines.append(f'- Active hours: {profile["active_hours"]}')
    lines.append('<!-- /pigeon:operator-state -->')
    return '\n'.join(lines)


def _upsert_block(text: str, start: str, end: str, block: str, anchor: str | None = None) -> str:
    pattern = _block_pattern(start, end)
    if pattern.search(text):
        return pattern.sub(block, text)
    if anchor and anchor in text:
        return _replace_or_insert_after_line(text, anchor, block)
    return text.rstrip() + '\n\n' + block + '\n'


def inject_prompt_telemetry(root: Path, snapshot: dict | None = None) -> bool:
    cp_path = root / COPILOT_PATH
    if not cp_path.exists():
        return False
    if snapshot is None:
        snapshot = _load_json(root / SNAPSHOT_PATH)
    if not snapshot:
        return False

    text = cp_path.read_text(encoding='utf-8')
    block = _render_prompt_block(snapshot)
    new_text = _upsert_block(
        text,
        PROMPT_BLOCK_START,
        PROMPT_BLOCK_END,
        block,
        anchor='<!-- /pigeon:operator-state -->',
    )
    if new_text != text:
        cp_path.write_text(new_text, encoding='utf-8')
    return True


def inject_auto_index(root: Path, registry: dict | None = None, processed: int = 0) -> bool:
    cp_path = root / COPILOT_PATH
    if not cp_path.exists() or not registry:
        return False
    text = cp_path.read_text(encoding='utf-8')
    block = _build_auto_index_block(root, registry, processed)
    new_text = _upsert_block(text, '<!-- pigeon:auto-index -->', '<!-- /pigeon:auto-index -->', block)
    if new_text != text:
        cp_path.write_text(new_text, encoding='utf-8')
    return True


def inject_bug_voices(root: Path, registry: dict | None = None) -> bool:
    cp_path = root / COPILOT_PATH
    if not cp_path.exists():
        return False
    text = cp_path.read_text(encoding='utf-8')
    block = _build_bug_voices_block(root, registry)
    new_text = _upsert_block(
        text,
        '<!-- pigeon:bug-voices -->',
        '<!-- /pigeon:bug-voices -->',
        block,
        anchor='<!-- /pigeon:auto-index -->',
    )
    if new_text != text:
        cp_path.write_text(new_text, encoding='utf-8')
    return True


def inject_operator_state(root: Path) -> bool:
    cp_path = root / COPILOT_PATH
    if not cp_path.exists():
        return False
    block = _build_operator_state_block(root)
    if not block:
        return False
    text = cp_path.read_text(encoding='utf-8')
    new_text = _upsert_block(
        text,
        '<!-- pigeon:operator-state -->',
        '<!-- /pigeon:operator-state -->',
        block,
        anchor='<!-- /pigeon:task-queue -->',
    )
    if new_text != text:
        cp_path.write_text(new_text, encoding='utf-8')
    return True


def audit_copilot_prompt(root: Path) -> dict:
    cp_path = root / COPILOT_PATH
    snapshot = _load_json(root / SNAPSHOT_PATH) or {}
    mutations = _load_json(root / 'logs' / 'copilot_prompt_mutations.json') or {}
    queue = _load_json(root / 'task_queue.json') or {}

    if not cp_path.exists():
        result = {
            'generated': datetime.now(timezone.utc).isoformat(),
            'missing_file': True,
            'missing_blocks': list(BLOCK_MARKERS.keys()),
            'unfilled_fields': ['copilot_instructions_missing'],
        }
        out_path = root / AUDIT_PATH
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        return result

    text = cp_path.read_text(encoding='utf-8')
    block_status = {}
    missing_blocks = []
    duplicate_blocks = []
    unfilled_fields = []
    extracted_blocks = {}

    for name, (start, end) in BLOCK_MARKERS.items():
        body = _extract_block(text, start, end)
        present = body is not None
        count = _count_blocks(text, start, end)
        block_status[name] = {'present': present, 'count': count}
        extracted_blocks[name] = body or ''
        if not present:
            missing_blocks.append(name)
        elif count > 1:
            duplicate_blocks.append(name)

    if 'Fresh start' in extracted_blocks.get('task_context', ''):
        unfilled_fields.append('task_context_placeholder')
    if 'Fresh start' in extracted_blocks.get('operator_state', ''):
        unfilled_fields.append('operator_state_placeholder')
    if 'Fresh start' in extracted_blocks.get('task_queue', '') and queue.get('tasks'):
        unfilled_fields.append('task_queue_not_reflecting_tasks')
    if block_status.get('prompt_telemetry', {}).get('present'):
        latest_preview = (((snapshot.get('latest_prompt') or {}).get('preview')) or '').strip()
        if latest_preview and latest_preview not in text:
            unfilled_fields.append('prompt_telemetry_stale')
    else:
        unfilled_fields.append('prompt_telemetry_missing')

    total_mutations = mutations.get('total_mutations', 0) if isinstance(mutations, dict) else 0
    if total_mutations == 0:
        unfilled_fields.append('mutation_tracking_empty')

    result = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'missing_file': False,
        'blocks': block_status,
        'missing_blocks': missing_blocks,
        'duplicate_blocks': duplicate_blocks,
        'unfilled_fields': unfilled_fields,
        'mutation_snapshots': total_mutations,
        'latest_prompt_preview': ((snapshot.get('latest_prompt') or {}).get('preview')),
    }
    out_path = root / AUDIT_PATH
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    return result


def refresh_managed_prompt(
    root: Path,
    snapshot: dict | None = None,
    track_mutations: bool = True,
    registry: dict | None = None,
    processed: int = 0,
) -> dict:
    root = Path(root)
    auto_index_refreshed = inject_auto_index(root, registry=registry, processed=processed)
    bug_voices_refreshed = inject_bug_voices(root, registry=registry)
    task_context_refreshed = _run_refresher(
        root,
        'src/推w_dp_s017*.py',
        'inject_task_context',
    )
    task_queue_refreshed = _run_refresher(
        root,
        'src/队p_tq_s018*.py',
        'inject_task_queue',
    )
    operator_state_refreshed = inject_operator_state(root)
    injected = inject_prompt_telemetry(root, snapshot=snapshot)

    mutation_result = None
    if track_mutations:
        try:
            import importlib.util

            recon_path = root / 'src' / 'prompt_recon_seq016_v001.py'
            if recon_path.exists():
                spec = importlib.util.spec_from_file_location('_prompt_recon_runtime_manager', recon_path)
                if spec is not None and spec.loader is not None:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    tracker = getattr(mod, 'track_copilot_prompt_mutations', None)
                    if callable(tracker):
                        mutation_result = tracker(root)
        except Exception:
            mutation_result = None

    audit = audit_copilot_prompt(root)
    return {
        'auto_index_refreshed': auto_index_refreshed,
        'bug_voices_refreshed': bug_voices_refreshed,
        'task_context_refreshed': task_context_refreshed,
        'task_queue_refreshed': task_queue_refreshed,
        'operator_state_refreshed': operator_state_refreshed,
        'prompt_telemetry_injected': injected,
        'mutation_result': mutation_result,
        'audit': audit,
    }


if __name__ == '__main__':
    import sys

    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    result = refresh_managed_prompt(root)
    print(json.dumps(result, indent=2, ensure_ascii=False))
