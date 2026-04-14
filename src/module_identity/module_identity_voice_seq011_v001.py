"""module_identity_voice_seq011_v001.py — Auto-extracted by Pigeon Compiler."""
import ast
import re

def _generate_voice(name: str, archetype: str, emotion: str,
                    entry: dict, lk: dict) -> str:
    ver = entry.get('ver', 1)
    tokens = entry.get('tokens', 0)
    heat = lk['heat'].get(name, {})
    hes = heat.get('avg_hes', 0) if heat else 0
    resolve = lk['_resolve']
    alias = resolve(name)
    graph = lk['graph'].get(name, {})
    if graph.get('degree', 0) == 0 and alias != name:
        graph = lk['graph'].get(alias, {})
    deaths = lk['deaths'].get(name, []) or lk['deaths'].get(alias, [])
    last_change = entry.get('last_change', '')
    importers = len(graph.get('edges_in', []))
    dependents = len(graph.get('edges_out', []))

    lines = []
    if archetype == 'veteran':
        lines.append(f"v{ver}. i've seen {ver} rewrites and survived them all.")
    elif archetype == 'hothead':
        lines.append(f"v{ver}. they keep changing me. something's never right.")
    elif archetype == 'ghost':
        lines.append("i exist but nobody calls me. silent in the graph.")
    elif archetype == 'anchor':
        lines.append(f"{importers} modules depend on me. no pressure.")
    elif archetype == 'orphan':
        lines.append("zero importers. maybe i'm dead. maybe not yet.")
    elif archetype == 'bloated':
        lines.append(f"{tokens} tokens and growing. split me before i collapse.")
    elif archetype == 'rookie':
        lines.append("v1. just got here. still learning the graph.")
    elif archetype == 'healer':
        lines.append("i scan for problems others create.")
    else:
        lines.append("steady. doing my job. nothing dramatic.")

    if emotion == 'frustrated':
        bugs = entry.get('bug_keys', [])
        lines.append(f"{len(bugs)} open bugs and a hesitation score of {hes:.2f}.")
    elif emotion == 'anxious':
        lines.append("entropy creeping up. uncertain about my own state.")
    elif emotion == 'manic':
        lines.append(f"high churn + cognitive load. operator struggles with me.")
    elif emotion == 'depressed':
        lines.append("untouched for a while. quiet.")

    if deaths:
        lines.append(f"i've died {len(deaths)} time(s). last cause: {deaths[-1]['cause']}.")
    if dependents > 3:
        lines.append(f"i import {dependents} modules. my dependency tree is wide.")
    if last_change:
        lines.append(f"last touched for: {last_change}")

    return ' '.join(lines)
