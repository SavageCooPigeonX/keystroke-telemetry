"""虚f_mc profile assembly — loads all data sources for a module."""
from __future__ import annotations

import json
from pathlib import Path


def _jload(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text('utf-8', errors='ignore'))
    except Exception:
        return None


def read_source(root: Path, rel_path: str, max_lines: int = 120) -> str:
    p = root / rel_path
    if not p.exists():
        return ''
    try:
        lines = p.read_text('utf-8', errors='ignore').splitlines()
        if len(lines) > max_lines:
            return '\n'.join(lines[:max_lines]) + f'\n# ... ({len(lines) - max_lines} more lines)'
        return '\n'.join(lines)
    except Exception:
        return ''


def is_real_module_name(name: str) -> bool:
    if len(name.split('_')) > 4:
        return False
    return True


def top_hesitation_files(root: Path, threshold: float, max_n: int) -> list[dict]:
    heat = _jload(root / 'file_heat_map.json') or {}
    items = []
    for name, v in heat.items():
        if not isinstance(v, dict):
            continue
        if not is_real_module_name(name):
            continue
        samples = v.get('samples', [])
        if len(samples) < 2:
            continue
        avg_hes = sum(s.get('hes', 0) for s in samples) / max(len(samples), 1)
        if avg_hes >= threshold:
            items.append({'module': name, 'avg_hes': round(avg_hes, 3), 'samples': len(samples)})
    return sorted(items, key=lambda x: x['avg_hes'], reverse=True)[:max_n]


def find_module_path(root: Path, module_name: str) -> str | None:
    reg = _jload(root / 'pigeon_registry.json')
    if reg:
        files = reg if isinstance(reg, list) else reg.get('files', [])
        for f in files:
            fname = f.get('file', '') or f.get('name', '')
            if module_name in fname:
                path = f.get('path', '')
                if path and (root / path).exists():
                    return path

    for search_dir in [root / 'src', root / 'pigeon_brain', root / 'pigeon_compiler']:
        if not search_dir.exists():
            continue
        for p in search_dir.rglob('*.py'):
            stem = p.stem
            if stem == module_name or stem.startswith(f'{module_name}_seq'):
                return str(p.relative_to(root))
        for p in search_dir.rglob('*.py'):
            stem = p.stem
            if module_name in stem:
                return str(p.relative_to(root))
    return None


def build_file_profile(root: Path, module_name: str, hes_score: float) -> dict:
    profile = {}

    mem = _jload(root / 'logs' / 'module_memory' / f'{module_name}.json')
    if mem:
        profile['version'] = mem.get('last_ver', '?')
        profile['tokens'] = mem.get('last_tokens', '?')
        profile['archetype'] = mem.get('last_archetype', 'unknown')
        profile['emotion'] = mem.get('last_emotion', 'unknown')
        profile['pass_count'] = mem.get('pass_count', 0)
        profile['bug_history'] = mem.get('bug_history', [])[-5:]
        profile['archetype_history'] = mem.get('archetype_history', [])[-5:]

    fp = _jload(root / 'file_profiles.json') or {}
    if module_name in fp:
        entry = fp[module_name]
        profile['partners'] = entry.get('partners', [])[:5]
        profile['fears'] = entry.get('fears', [])
        profile['personality'] = entry.get('personality', 'unknown')

    bugs = _jload(root / 'logs' / 'bug_profiles.json') or {}
    all_mods = bugs.get('all_modules', {})
    if module_name in all_mods:
        b = all_mods[module_name]
        profile['current_bugs'] = b.get('bug_keys', [])
        profile['dossier_score'] = b.get('dossier_score', 0)

    sfa = _jload(root / 'logs' / 'self_fix_accuracy.json') or {}
    persistent = sfa.get('persistent_top_10', [])
    mod_bugs = [p for p in persistent if p.get('module') == module_name]
    if mod_bugs:
        profile['chronic_bugs'] = mod_bugs

    emap = _jload(root / 'logs' / 'entropy_map.json') or {}
    for entry in emap.get('top_entropy_modules', []):
        if entry.get('module') == module_name:
            profile['entropy'] = entry.get('avg_entropy', 0)
            profile['entropy_samples'] = entry.get('samples', 0)
            break

    mod_path = find_module_path(root, module_name)
    if mod_path:
        profile['source_path'] = mod_path
        profile['source'] = read_source(root, mod_path)

    profile['hesitation'] = hes_score
    return profile
