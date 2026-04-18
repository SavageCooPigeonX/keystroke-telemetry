"""module_identity_seq001_v001_todo_seq012_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 012 | VER: v001 | 41 lines | ~459 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def _generate_todo(name: str, entry: dict, lk: dict) -> list[str]:
    """Self-generated TODO list based on current signals."""
    todos = []
    tokens = entry.get('tokens', 0)
    bugs = entry.get('bug_keys', [])
    resolve = lk['_resolve']
    alias = resolve(name)
    graph = lk['graph'].get(name, {})
    if graph.get('degree', 0) == 0 and alias != name:
        graph = lk['graph'].get(alias, {})
    deaths = lk['deaths'].get(name, []) or lk['deaths'].get(alias, [])
    dossier = lk['dossier'].get(name, {}) or lk['dossier'].get(alias, {})

    if tokens > 3000:
        todos.append(f'split me — {tokens} tokens is over cap')
    if 'oc' in bugs:
        todos.append('pigeon compiler needs to decompose me')
    if 'hi' in bugs or 'hardcoded_import' in str(bugs):
        todos.append('fix my hardcoded imports')
    if 'de' in bugs or 'dead_export' in str(bugs):
        todos.append('remove dead exports nobody uses')
    if deaths:
        causes = set(d['cause'] for d in deaths)
        todos.append(f'investigate deaths: {", ".join(causes)}')
    if dossier.get('recur', 0) >= 3:
        todos.append(f'recurring issue ({dossier["recur"]}x) — needs structural fix')
    if len(graph.get('edges_in', [])) == 0 and entry.get('ver', 1) >= 2:
        todos.append('nobody imports me — verify if still needed')

    partners = lk['profiles'].get(name, {}).get('partners', [])
    if not partners:
        partners = lk['profiles'].get(resolve(name), {}).get('partners', [])
    high_coupling = [p for p in partners if p.get('score', 0) >= 0.7]
    if high_coupling:
        names = ', '.join(p['name'] for p in high_coupling[:2])
        todos.append(f'high coupling with {names} — consider merging or decoupling')

    return todos
