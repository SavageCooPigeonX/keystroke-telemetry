"""module_identity_classify_seq010_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def _classify_archetype(entry: dict, lk: dict, name: str) -> str:
    ver = entry.get('ver', 1)
    tokens = entry.get('tokens', 0)
    resolve = lk['_resolve']
    alias = resolve(name)
    graph = lk['graph'].get(name, {})
    if graph.get('degree', 0) == 0 and alias != name:
        graph = lk['graph'].get(alias, {})
    importers = len(graph.get('edges_in', []))
    hes = lk['heat'].get(name, {}).get('avg_hes', 0)
    bugs = entry.get('bug_keys', [])
    profile = lk['profiles'].get(name, {})

    if importers == 0 and ver <= 1 and tokens < 200:
        return 'orphan'
    if tokens > 3000:
        return 'bloated'
    if ver >= 8 and hes > 0.5:
        return 'hothead'
    if ver >= 6:
        return 'veteran'
    if importers >= 5:
        return 'anchor'
    if ver == 1:
        return 'rookie'
    if any('self_fix' in b or 'heal' in b for b in bugs):
        return 'healer'
    if hes == 0 and ver <= 2 and tokens < 500:
        return 'ghost'
    return 'stable'


def _classify_emotion(entropy: float, hes: float, bug_count: int,
                      churn: int, death_count: int) -> str:
    if bug_count >= 3 and hes > 0.6:
        return 'frustrated'
    if death_count >= 2:
        return 'frustrated'
    if entropy > 0.35:
        return 'anxious'
    if hes > 0.7 and churn > 5:
        return 'manic'
    if hes == 0 and churn <= 1 and bug_count == 0:
        return 'depressed'
    if entropy < 0.2 and bug_count == 0 and death_count == 0:
        return 'confident'
    return 'serene'
