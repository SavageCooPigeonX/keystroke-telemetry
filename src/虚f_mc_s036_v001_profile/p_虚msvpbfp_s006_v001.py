"""虚f_mc_s036_v001_profile_build_file_profile_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 51 lines | ~530 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

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

    bugs = _jload(root / 'logs' / 'bug_profiles_seq001_v001.json') or {}
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
