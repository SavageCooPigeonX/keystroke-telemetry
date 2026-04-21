"""管w_cpm_bvx_s013_v001.py — bug voices block builder.

Builds the <!-- pigeon:bug-voices --> block from registry bug data.
Self-contained: duplicates small utilities to avoid circular imports.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 013 | VER: v001 | 127 lines | ~1,246 tokens
# DESC:   bug_voices_block_builder
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from __future__ import annotations

import json
from pathlib import Path

# ── duplicated constants ──────────────────────────────────────────────────────
_COPILOT_PATH = '.github/copilot-instructions.md'

# ── bug data tables ───────────────────────────────────────────────────────────
_BUG_KEY_ORDER = ('oc', 'hi', 'hc', 'de', 'dd', 'qn')

_BUG_PERSONAS: dict[str, tuple[str, str]] = {
    'hi': ('Hardcode Gremlin', 'I weld imports to exact paths and squeal when rename day comes.'),
    'de': ('Dead Export Shade', 'I leave dead functions standing so everyone thinks they still matter.'),
    'dd': ('Mirror Imp', 'I duplicate the same explanation until nobody remembers which copy was first.'),
    'hc': ('Coupling Leech', 'I braid modules together until one cut hurts five files.'),
    'oc': ('Overcap Maw', 'I keep swelling this file past the hard cap. Split me before I eat context.'),
    'qn': ('Noise Imp', 'I fog the query stream until the real intent has to fight to stay visible.'),
}

# ── duplicated micro-utilities ────────────────────────────────────────────────

def _load_json(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None


def _registry_items(registry: dict | None) -> list[tuple[str, dict]]:
    if not registry:
        return []
    if isinstance(registry, dict) and isinstance(registry.get('files'), list):
        return [(e.get('path', ''), e) for e in registry['files'] if isinstance(e, dict)]
    if isinstance(registry, dict):
        return [(p, e) for p, e in registry.items() if isinstance(e, dict)]
    return []

# ── bug voice helpers ─────────────────────────────────────────────────────────

def _primary_bug(entry: dict) -> str:
    keys = [key for key in entry.get('bug_keys', []) if key]
    counts = entry.get('bug_counts', {}) or {}
    if not keys:
        return ''
    order = {key: idx for idx, key in enumerate(_BUG_KEY_ORDER)}
    return max(keys, key=lambda k: (int(counts.get(k, 0)), -order.get(k, len(order)), k))


def _bug_voice_score(entry: dict) -> int:
    counts = entry.get('bug_counts', {}) or {}
    active = [k for k in entry.get('bug_keys', []) if k]
    return len(active) * 10 + sum(int(counts.get(k, 0)) for k in active)

# ── builder ───────────────────────────────────────────────────────────────────

def _build_bug_voices_block(root: Path, registry: dict | None) -> str:
    try:
        from src.self_fix_tracker_seq001_v001 import build_narrative_block
        narrative = build_narrative_block(root)
        if narrative:
            return narrative
    except Exception:
        pass

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
        others = [b for b in entry.get('bug_keys', []) if b != key]
        others_s = f' other={"+".join(others)}' if others else ''
        mark = entry.get('last_bug_mark', 'unmarked')
        lc = entry.get('last_change', '')
        lc_s = f' last={lc}' if lc else ''
        lines.append(
            f'- `{entry.get("name", "?")}` {mark} · {key} `{entity}` x{recur}{others_s}: "{voice}"{lc_s}'
        )

    lines.append('<!-- /pigeon:bug-voices -->')
    return '\n'.join(lines)


def inject_bug_voices(root: Path, registry: dict | None = None) -> bool:
    import re as _re
    cp_path = root / _COPILOT_PATH
    if not cp_path.exists():
        return False
    text = cp_path.read_text(encoding='utf-8')
    block = _build_bug_voices_block(root, registry)
    pattern = _re.compile(
        r'(?ms)^\s*<!-- pigeon:bug-voices -->\s*$\n.*?^\s*<!-- /pigeon:bug-voices -->\s*$'
    )
    if pattern.search(text):
        new_text = pattern.sub(block, text)
    else:
        new_text = text.rstrip() + '\n\n' + block + '\n'
    if new_text != text:
        cp_path.write_text(new_text, encoding='utf-8')
    return True
