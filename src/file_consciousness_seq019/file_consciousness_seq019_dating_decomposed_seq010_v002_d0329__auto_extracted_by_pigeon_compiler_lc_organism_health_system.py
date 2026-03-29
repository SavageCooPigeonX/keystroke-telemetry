"""file_consciousness_seq019_dating_decomposed_seq010_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 010 | VER: v002 | 87 lines | ~807 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: organism_health_system
# LAST:   2026-03-29 @ 1f4291d
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re

def build_dating_profiles(root: Path) -> dict:
    """Build compatibility scores for all tracked pigeon modules.

    Uses: registry for module list, import_tracer for data flow,
    heat map for co-stress patterns, registry version count for drama.
    Returns {module_name: {personality, partners: [{name, score, reason}], fears}}.
    """
    reg_path = root / 'pigeon_registry.json'
    heat_path = root / 'file_heat_map.json'
    if not reg_path.exists():
        return {}

    reg = json.loads(reg_path.read_text('utf-8'))
    files = reg.get('files', [])
    heat = json.loads(heat_path.read_text('utf-8')) if heat_path.exists() else {}

    # Build import graph: {module_stem: [modules_it_imports]}
    import_graph = {}
    for entry in files:
        p = root / entry['path']
        if not p.exists():
            continue
        try:
            src = p.read_text('utf-8', errors='ignore')
        except Exception:
            continue
        imports = set()
        for m in re.finditer(r'^(?:from|import)\s+(\S+)', src, re.M):
            mod = m.group(1).split('.')[0]
            imports.add(mod)
        import_graph[entry['name']] = imports

    profiles = {}
    for entry in files:
        name = entry['name']
        ver = entry.get('ver', 1)
        tokens = entry.get('tokens', 0)
        hm = heat.get(name, {})

        # Find partners via shared imports (bidirectional edges)
        partners = []
        my_imports = import_graph.get(name, set())
        for other_name, their_imports in import_graph.items():
            if other_name == name:
                continue
            # Physical attraction: data flow overlap
            flow = len(my_imports & their_imports)
            # Trauma bonding: both high-version (pain points)
            other_entry = next((f for f in files if f['name'] == other_name), {})
            other_ver = other_entry.get('ver', 1)
            drama = min(ver, other_ver) / max(ver + other_ver, 1)
            # Combined score
            score = round(0.6 * min(flow / 3, 1.0) + 0.4 * drama, 2)
            if score > 0.1:
                reason = f'{flow} shared imports'
                if drama > 0.3:
                    reason += f', both high-churn (v{ver}+v{other_ver})'
                partners.append({'name': other_name, 'score': score, 'reason': reason})

        partners.sort(key=lambda p: p['score'], reverse=True)

        # Consciousness summary for this file
        p = root / entry['path']
        fears = []
        if p.exists():
            try:
                fc = build_file_consciousness(p)
                for fn in fc.get('functions', []):
                    fears.extend(fn.get('i_fear', []))
            except Exception:
                pass

        profiles[name] = {
            'personality': 'veteran' if ver >= 5 else 'stable' if ver >= 3 else 'fresh',
            'version': ver,
            'tokens': tokens,
            'partners': partners[:5],
            'fears': list(dict.fromkeys(fears))[:6],
            'avg_hes': _safe_hes(hm),
        }

    return profiles
