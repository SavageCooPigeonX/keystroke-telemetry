"""module_identity_lookups_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 105 lines | ~966 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import ast
import re

def _build_lookups(sources: dict) -> dict:
    """Pre-process sources into fast lookup dicts keyed by module name."""
    lk = {}
    aliases = _build_alias_map(sources)
    lk['aliases'] = aliases

    def _resolve(name):
        """Return the name that has data in the source."""
        return aliases.get(name, name)

    # Entropy: module -> {avg_entropy, samples, hedges, shed_conf}
    ent = {}
    for mod in sources['entropy_map'].get('top_entropy_modules', []):
        ent[mod['module']] = {
            'avg_entropy': mod.get('avg_entropy', 0),
            'samples': mod.get('samples', 0),
            'hedges': mod.get('hedges', 0),
            'shed_conf': mod.get('shed_avg_confidence'),
        }
    lk['entropy'] = ent

    # Heat: module -> {avg_hes, samples, dominant_state, states, raw_samples}
    heat = {}
    for mod_name, data in sources['heat_map'].items():
        samples = data.get('samples', [])
        if samples:
            avg_hes = sum(s.get('hes', 0) for s in samples) / len(samples)
            states = {}
            for s in samples:
                st = s.get('state', 'unknown')
                states[st] = states.get(st, 0) + 1
            dominant = max(states, key=states.get) if states else 'unknown'
            heat[mod_name] = {
                'avg_hes': round(avg_hes, 3),
                'samples': len(samples),
                'dominant_state': dominant,
                'states': states,
                'raw_samples': samples,
            }
    lk['heat'] = heat

    # Numeric surface: module -> {edges_in, edges_out, degree, heat, dual_score}
    graph = {}
    for mod_name, node in sources['numeric_surface'].get('nodes', {}).items():
        graph[mod_name] = {
            'edges_in': node.get('edges_in', []),
            'edges_out': node.get('edges_out', []),
            'degree': node.get('degree', 0),
            'heat': node.get('heat', 0),
            'dual_score': node.get('dual_score', 0),
        }
    lk['graph'] = graph
    lk['_resolve'] = _resolve

    # Bug profiles: module -> {bugs, counts, entities, last_mark, dossier_score}
    bugs = {}
    for mod_name, bdata in sources['bug_profiles'].get('all_modules', {}).items():
        bugs[mod_name] = {
            'bug_keys': bdata.get('bug_keys', []),
            'bug_counts': bdata.get('bug_counts', {}),
            'bug_entities': bdata.get('bug_entities', {}),
            'last_bug_mark': bdata.get('last_bug_mark', ''),
            'last_change': bdata.get('last_change', ''),
            'dossier_score': bdata.get('dossier_score', 0),
        }
    lk['bugs'] = bugs

    # File profiles: module -> {personality, partners, fears}
    profiles = {}
    for mod_name, fdata in sources['file_profiles'].items():
        profiles[mod_name] = {
            'personality': fdata.get('personality', ''),
            'partners': fdata.get('partners', []),
            'fears': fdata.get('fears', []),
        }
    lk['profiles'] = profiles

    # Death log: module -> list of deaths
    deaths = {}
    death_list = sources['death_log'] if isinstance(sources['death_log'], list) else []
    for d in death_list:
        node = d.get('node', '')
        deaths.setdefault(node, []).append({
            'cause': d.get('cause', ''),
            'severity': d.get('severity', ''),
            'detail': d.get('detail', ''),
            'ts': d.get('ts', ''),
        })
    lk['deaths'] = deaths

    # Dossier: module -> {score, recur, bugs}
    dossier = {}
    for d in sources['dossier'].get('dossiers', []):
        dossier[d.get('file', '')] = {
            'score': d.get('score', 0),
            'recur': d.get('recur', 0),
            'bugs': d.get('bugs', []),
        }
    lk['dossier'] = dossier

    return lk
