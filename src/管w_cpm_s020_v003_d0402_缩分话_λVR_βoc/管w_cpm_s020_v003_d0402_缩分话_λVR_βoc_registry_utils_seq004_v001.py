"""管w_cpm_s020_v003_d0402_缩分话_λVR_βoc_registry_utils_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

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
