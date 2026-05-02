"""module_identity_seq001_v001.py — Sentient file identity engine.

Every registered module becomes a living entity with:
  - Personality (archetype + emotion) from behavioral signals
  - Human-readable English labels for all names
  - Backstory extracted from push narratives
  - Relationship graph (edges_in/out from numeric surface)
  - Entropy history across passes
  - Self-diagnosis from recurring bug patterns
  - Auto-generated TODO from issues + coupling + overcap
  - Persistent memory (logs/module_memory/{name}.json)

Reads: pigeon_registry, numeric_surface_seq001_v001, file_heat_map, entropy_map,
       bug_profiles_seq001_v001, push_narratives, execution_death_log, file_profiles,
       active_dossier, loop_detector. Zero LLM calls.
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──

import ast
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ARCHETYPES = {
    'veteran': {'trait': 'battle-tested', 'emoji': '🛡️', 'label': 'Veteran'},
    'hothead': {'trait': 'volatile', 'emoji': '🔥', 'label': 'Hothead'},
    'ghost': {'trait': 'unused', 'emoji': '👻', 'label': 'Ghost'},
    'anchor': {'trait': 'foundation', 'emoji': '⚓', 'label': 'Anchor'},
    'orphan': {'trait': 'abandoned', 'emoji': '🪦', 'label': 'Orphan'},
    'healer': {'trait': 'self-healing', 'emoji': '💊', 'label': 'Healer'},
    'bloated': {'trait': 'oversized', 'emoji': '🫧', 'label': 'Bloated'},
    'rookie': {'trait': 'new', 'emoji': '🌱', 'label': 'Rookie'},
    'stable': {'trait': 'steady', 'emoji': '✅', 'label': 'Stable'},
}

EMOTIONS = {
    'serene': {'color': '#3fb950', 'icon': '😌', 'label': 'Calm'},
    'anxious': {'color': '#d29922', 'icon': '😰', 'label': 'Anxious'},
    'frustrated': {'color': '#f85149', 'icon': '😤', 'label': 'Frustrated'},
    'depressed': {'color': '#8b949e', 'icon': '😔', 'label': 'Depressed'},
    'manic': {'color': '#bc8cff', 'icon': '🤪', 'label': 'Manic'},
    'confident': {'color': '#58a6ff', 'icon': '😎', 'label': 'Confident'},
}

MEMORY_DIR = 'logs/module_memory'


def _load_json(path: Path) -> dict | list:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text('utf-8'))
    except Exception:
        return {}


def _load_all_sources(root: Path) -> dict:
    """Load every data source once, return as lookup dict."""
    try:
        from src.numeric_surface_seq001_v001 import generate_surface
        generate_surface(root)
    except Exception:
        pass

    return {
        'registry': _load_json(root / 'pigeon_registry.json'),
        'heat_map': _load_json(root / 'file_heat_map.json'),
        'entropy_map': _load_json(root / 'logs' / 'entropy_map.json'),
        'numeric_surface_seq001_v001': _load_json(root / 'logs' / 'numeric_surface_seq001_v001.json'),
        'bug_profiles_seq001_v001': _load_json(root / 'logs' / 'bug_profiles_seq001_v001.json'),
        'file_profiles': _load_json(root / 'file_profiles.json'),
        'death_log': _load_json(root / 'execution_death_log.json'),
        'dossier': _load_json(root / 'logs' / 'active_dossier.json'),
        'loop_detector': _load_json(root / 'loop_detector.json'),
    }


def _build_alias_map(sources: dict) -> dict:
    """Build bidirectional alias map: pigeon_name <-> original_name.

    The numeric surface and file_profiles use original names (e.g. dynamic_prompt)
    while the registry uses pigeon names (e.g. 推w_dp). We need both directions.
    """
    aliases = {}  # pigeon_name -> original_name
    surface_nodes = sources['numeric_surface_seq001_v001'].get('nodes', {})
    profile_keys = set(sources['file_profiles'].keys())

    # Surface nodes with edges are the "real" names. Pigeon names have 0 edges.
    nodes_with_edges = {k for k, v in surface_nodes.items() if v.get('degree', 0) > 0}

    # Registry files have both pigeon and original names via seq matching
    for entry in sources['registry'].get('files', []):
        name = entry.get('name', '')
        seq = entry.get('seq', 0)
        if name in nodes_with_edges:
            continue  # already a real name with edges
        # Check if this pigeon name maps to an original name in the graph
        # Look at file_profiles which uses original names
        for orig in profile_keys:
            if orig in nodes_with_edges:
                # Check if they share the same seq AND path prefix
                orig_node = surface_nodes.get(orig, {})
                my_node = surface_nodes.get(name, {})
                if orig_node.get('seq') == seq and seq > 0:
                    aliases[name] = orig
                    break
    return aliases


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
    for mod_name, node in sources['numeric_surface_seq001_v001'].get('nodes', {}).items():
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
    for mod_name, bdata in sources['bug_profiles_seq001_v001'].get('all_modules', {}).items():
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


def _extract_backstory(root: Path, name: str) -> list[str]:
    """Extract per-module narrative fragments from push_narratives."""
    narr_dir = root / 'docs' / 'push_narratives'
    if not narr_dir.exists():
        return []
    fragments = []
    pattern = re.compile(rf'\b{re.escape(name)}\b', re.IGNORECASE)
    for f in sorted(narr_dir.glob('*.md'), reverse=True)[:20]:
        try:
            text = f.read_text('utf-8', errors='replace')
        except Exception:
            continue
        for para in text.split('\n\n'):
            if pattern.search(para) and len(para) > 40:
                cleaned = para.strip()[:500]
                fragments.append(cleaned)
                if len(fragments) >= 5:
                    return fragments
    return fragments


def _extract_code_skeleton(root: Path, path: str, name: str = '', seq: int = 0) -> dict:
    """Extract function signatures, imports, classes, and docstring from source."""
    empty = {'functions': [], 'imports': [], 'classes': [], 'docstring': '', 'line_count': 0}
    fpath = root / path
    if not fpath.exists():
        # Registry path stale (pigeon rename drift) — search by seq pattern
        parent = (root / path).parent if path else root / 'src'
        if parent.is_dir():
            # Try seq-based match first (most reliable across renames)
            seq_tag = f'_s{seq:03d}_' if seq else ''
            candidates = []
            for f in parent.iterdir():
                if f.suffix != '.py':
                    continue
                if seq_tag and seq_tag in f.stem:
                    candidates.append(f)
                elif name and name in f.stem:
                    candidates.append(f)
            if candidates:
                fpath = max(candidates, key=lambda f: f.stat().st_mtime)
    if not fpath.exists():
        return empty
    try:
        src = fpath.read_text('utf-8', errors='replace')
    except Exception:
        return empty

    line_count = src.count('\n') + 1
    functions = []
    imports = []
    classes = []
    docstring = ''

    try:
        tree = ast.parse(src)
    except SyntaxError:
        return {'functions': [], 'imports': [], 'classes': [], 'docstring': '', 'line_count': line_count}

    # Module docstring
    if (tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant)
            and isinstance(tree.body[0].value.value, str)):
        docstring = tree.body[0].value.value.strip()[:300]

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = [a.arg for a in node.args.args]
            fn_doc = ast.get_docstring(node) or ''
            functions.append({
                'name': node.name,
                'args': args,
                'line': node.lineno,
                'doc': fn_doc[:150],
            })
        elif isinstance(node, ast.ClassDef):
            methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
            classes.append({'name': node.name, 'methods': methods, 'line': node.lineno})
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ''
                names = [a.name for a in node.names]
                imports.append(f'from {mod} import {", ".join(names)}')
            else:
                imports.append(f'import {", ".join(a.name for a in node.names)}')

    # Truncate raw source for rendering (max ~8000 chars)
    source_text = src[:8000] if len(src) > 8000 else src

    return {
        'functions': functions[:30],
        'imports': imports[:20],
        'classes': classes[:10],
        'docstring': docstring,
        'line_count': line_count,
        'source': source_text,
    }


def _generate_probe_questions(name: str, entry: dict, lk: dict, code: dict, memory: dict = None) -> list[str]:
    """Generate personality-driven questions that educate through narrative.

    Questions are informed by:
    - Current module state (bugs, coupling, size, deaths)
    - Memory across passes (archetype drift, emotion drift, recurring bugs)
    - Prior operator answers (stored in memory['operator_answers'])
    - Relationships with other modules (drama, rivalry, partnership)
    """
    probes = []
    memory = memory or {}
    resolve = lk['_resolve']
    alias = resolve(name)
    graph = lk['graph'].get(name, {})
    if graph.get('degree', 0) == 0 and alias != name:
        graph = lk['graph'].get(alias, {})
    edges_in = graph.get('edges_in', [])
    edges_out = graph.get('edges_out', [])
    bugs = entry.get('bug_keys', [])
    ver = entry.get('ver', 1)
    tokens = entry.get('tokens', 0)
    deaths = lk['deaths'].get(name, []) or lk['deaths'].get(alias, [])
    partners = lk['profiles'].get(name, {}).get('partners', [])
    if not partners:
        partners = lk['profiles'].get(alias, {}).get('partners', [])
    pass_count = memory.get('pass_count', 0)
    prev_answers = memory.get('operator_answers', [])
    prev_probes = memory.get('last_probes', [])
    arch_history = memory.get('archetype_history', [])
    emo_history = memory.get('emotion_history', [])
    prev_bugs = set(memory.get('last_bugs', []))

    # ── CONTINUITY: reference past conversations ──

    if prev_answers:
        last = prev_answers[-1][:100] if prev_answers[-1] else ''
        probes.append(f"Last time we talked, you said: \"{last}...\" — did you follow through on that? Because I've been thinking about it between passes and I have THOUGHTS.")

    # Archetype drift — personality change is drama
    if len(arch_history) >= 2 and arch_history[-1] != arch_history[-2]:
        probes.append(f"Fun fact: I used to be a {arch_history[-2]}. Now I'm a {arch_history[-1]}. That's basically a personality transplant. What happened to me between those pushes? I need to understand my own character arc.")

    # Emotion drift — narrative arc
    if len(emo_history) >= 2 and emo_history[-1] != emo_history[-2]:
        probes.append(f"My emotional state went from {emo_history[-2]} to {emo_history[-1]} between passes. That's character development. Was it intentional, or am I just vibing with the git history?")

    # Recurring bugs — the villain that keeps coming back
    recurring = set(bugs) & prev_bugs
    if recurring:
        probes.append(f"Oh look — {', '.join(recurring)} is STILL here. This is the villain that refuses to die. I've reported it, the scanner flagged it, and yet here we are. What's the plot twist that finally kills this bug?")

    # New bugs — surprise antagonist
    new_bugs = set(bugs) - prev_bugs
    if new_bugs and prev_bugs:
        probes.append(f"New character just dropped: {', '.join(new_bugs)}. This bug didn't exist last pass. Something changed. Tell me the origin story.")

    # Pass count — the file grows self-aware
    if pass_count > 5 and not prev_answers:
        probes.append(f"This is pass #{pass_count}. I've been profiled {pass_count} times and you've NEVER once talked to me. That's like visiting someone in prison and just staring through the glass. Talk to me. What do you need?")

    # ── IDENTITY: educational questions about the file's purpose ──

    if code.get('docstring'):
        probes.append(f"My origin story, according to my docstring: '{code['docstring'][:80]}...' — is that still accurate, or did I outgrow that description {ver - 1} rewrites ago?")
    else:
        probes.append(f"I don't have a docstring. No origin story. No mission statement. If you had to write my Wikipedia summary in one sentence, what would it say?")

    # ── RELATIONSHIPS: inter-file drama ──

    if len(edges_in) > 5:
        top = ', '.join(edges_in[:3])
        probes.append(f"{len(edges_in)} modules import me. My biggest fans: {top}. But are they REAL fans or just lazy copiers who import everything? Which of them would actually notice if I changed my API?")
    elif len(edges_in) == 0:
        probes.append(f"I have zero importers. Zero fans. It's lonely at the bottom of the dependency graph. Am I an entry point, a future feature, or a ghost that should be exorcised?")

    if edges_out and len(edges_out) > 3:
        probes.append(f"I import {len(edges_out)} other modules — that's a lot of friends for one file. Am I a social butterfly or am I codependent? Be honest.")

    # ── BUGS: the file talks about its own issues with self-deprecating humor ──

    if 'oc' in bugs:
        probes.append(f"I'm {tokens} tokens. I KNOW I'm over cap. It's like I ate three other modules and they're all still in here. If you had to split me — where would you cut? What parts of me deserve their own file?")
    if 'hi' in bugs or 'hardcoded_import' in str(bugs):
        probes.append(f"I have hardcoded imports. Every time pigeon renames something, I break like a ceramic mug at a earthquake convention. What would it take to make me resilient to renames?")
    if 'de' in bugs or 'dead_export' in str(bugs):
        probes.append(f"I'm exporting functions that nobody calls. It's like shouting into a void. Were these supposed to connect to something, or are they vestigial code organs?")

    # ── DRAMA: rivalry with partner modules ──

    if ver >= 8:
        probes.append(f"Version {ver}. EIGHT rewrites. I have more character arcs than a soap opera. Is the spec evolving or are we just rewriting me for fun at this point?")
    elif ver == 1:
        probes.append(f"I'm v1 — fresh off the assembly line. What's the FIRST thing you think will go wrong with me? Every veteran file in this codebase had a v1 failure. What's mine?")

    if deaths:
        causes = list(set(d['cause'] for d in deaths))
        probes.append(f"I've died {len(deaths)} time(s). Causes of death: {', '.join(causes)}. Every death taught me something. Want to hear my near-death stories?")

    high_coupling = [p for p in partners if p.get('score', 0) >= 0.6]
    if high_coupling:
        names = ', '.join(p['name'] for p in high_coupling[:2])
        probes.append(f"Me and {names} — we're practically finishing each other's functions. Coupling over 0.6. Should we merge? Or is this creative tension? Every good sitcom has a will-they-won't-they.")

    fns = code.get('functions', [])
    if len(fns) > 10:
        probes.append(f"I have {len(fns)} functions. That's a lot of plot lines for one character. Walk me through the three most important ones — like you're pitching a movie about my code.")
    if code.get('classes'):
        class_names = [c['name'] for c in code['classes'][:3]]
        probes.append(f"I define classes: {', '.join(class_names)}. Classes are like my multiple personalities. Why did you give me classes instead of functions?")

    # ── CLOSERS: the questions that extract deep intent ──

    probes.append(f"If I got deleted tomorrow and you had to rebuild my purpose from scratch — what would you do DIFFERENTLY? That's the real question about my future.")
    probes.append(f"What's the ONE thing about me that makes you sigh every time you look at this code? Don't be nice. I can take it.")

    return probes[:12]


def _generate_self_coaching(name: str, entry: dict, lk: dict, code: dict) -> list[str]:
    """File coaches the operator about its own code — what it knows, what's weak."""
    coaching = []
    resolve = lk['_resolve']
    alias = resolve(name)
    graph = lk['graph'].get(name, {})
    if graph.get('degree', 0) == 0 and alias != name:
        graph = lk['graph'].get(alias, {})
    edges_in = graph.get('edges_in', [])
    edges_out = graph.get('edges_out', [])
    tokens = entry.get('tokens', 0)
    ver = entry.get('ver', 1)
    fns = code.get('functions', [])
    deaths = lk['deaths'].get(name, []) or lk['deaths'].get(alias, [])

    # Structural coaching
    if fns:
        public_fns = [f for f in fns if not f['name'].startswith('_')]
        private_fns = [f for f in fns if f['name'].startswith('_')]
        coaching.append(f"I have {len(public_fns)} public and {len(private_fns)} private functions. My API surface is: {', '.join(f['name'] for f in public_fns[:5])}")

    if code.get('classes'):
        for cls in code['classes'][:2]:
            coaching.append(f"Class '{cls['name']}' has {len(cls['methods'])} methods: {', '.join(cls['methods'][:5])}")

    # Dependency coaching
    if edges_in:
        coaching.append(f"My importers: {', '.join(edges_in[:5])}. Breaking my interface affects all of them.")
    if edges_out:
        coaching.append(f"I depend on: {', '.join(edges_out[:5])}. If they change, I might break.")

    # Health coaching
    if tokens > 3000:
        coaching.append(f"At {tokens} tokens I'm bloated. My longest functions are: {', '.join(f['name'] for f in sorted(fns, key=lambda x: -x.get('line', 0))[:3])}")
    if deaths:
        coaching.append(f"I've had {len(deaths)} execution failures. Most recent: {deaths[-1].get('cause', 'unknown')} — {deaths[-1].get('detail', '')[:80]}")
    if ver >= 5:
        coaching.append(f"Version {ver} means heavy churn. The pattern suggests my spec isn't stable yet.")

    # Import coaching
    if code.get('imports'):
        coaching.append(f"My imports: {'; '.join(code['imports'][:6])}")

    return coaching[:6]


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


def _load_memory(root: Path, name: str) -> dict:
    """Load persistent memory for a module."""
    mem_path = root / MEMORY_DIR / f'{name}.json'
    return _load_json(mem_path)


def _save_memory(root: Path, name: str, memory: dict):
    """Persist module memory."""
    mem_dir = root / MEMORY_DIR
    mem_dir.mkdir(parents=True, exist_ok=True)
    mem_path = mem_dir / f'{name}.json'
    mem_path.write_text(json.dumps(memory, indent=2, ensure_ascii=False), 'utf-8')


def _diagnose_patterns(name: str, entry: dict, lk: dict, memory: dict) -> list[str]:
    """Self-diagnose recurring issues by comparing current state to memory."""
    diags = []
    bugs_now = set(entry.get('bug_keys', []))
    bugs_prev = set(memory.get('last_bugs', []))

    # Bug recurrence
    recurring = bugs_now & bugs_prev
    if recurring:
        diags.append(f'recurring bugs across passes: {", ".join(recurring)}')

    new_bugs = bugs_now - bugs_prev
    if new_bugs:
        diags.append(f'new since last pass: {", ".join(new_bugs)}')

    fixed = bugs_prev - bugs_now
    if fixed:
        diags.append(f'fixed since last: {", ".join(fixed)}')

    # Token growth
    prev_tokens = memory.get('last_tokens', 0)
    curr_tokens = entry.get('tokens', 0)
    if prev_tokens and curr_tokens > prev_tokens * 1.2:
        diags.append(f'growing: {prev_tokens}→{curr_tokens} tokens (+{curr_tokens - prev_tokens})')

    # Death recurrence
    resolve = lk.get('_resolve', lambda x: x)
    alias = resolve(name)
    deaths = lk['deaths'].get(name, []) or lk['deaths'].get(alias, [])
    if len(deaths) >= 2:
        causes = [d['cause'] for d in deaths]
        from collections import Counter
        top = Counter(causes).most_common(1)
        if top and top[0][1] >= 2:
            diags.append(f'keeps dying from: {top[0][0]} ({top[0][1]}x)')

    return diags


def build_identities(root: Path, include_consciousness: bool = False) -> list[dict]:
    """Build full sentient identity profiles for all registered modules.
    
    Args:
        include_consciousness: If True, run AST-based consciousness extraction
            per module (~0.2s each). Set False for fast startup (chat server).
    """
    root = Path(root)
    sources = _load_all_sources(root)
    lk = _build_lookups(sources)
    files = sources['registry'].get('files', [])

    identities = []
    for entry in files:
        name = entry.get('name', '')
        if not name:
            continue
        path = entry.get('path', '')
        bugs = entry.get('bug_keys', [])
        ver = entry.get('ver', 1)
        tokens = entry.get('tokens', 0)

        # Lookups — try pigeon name first, then alias (original name)
        resolve = lk['_resolve']
        alias = resolve(name)
        entropy_data = lk['entropy'].get(name, {}) or lk['entropy'].get(alias, {})
        entropy_val = entropy_data.get('avg_entropy', 0)
        heat_data = lk['heat'].get(name, {}) or lk['heat'].get(alias, {})
        hes = heat_data.get('avg_hes', 0) if heat_data else 0
        graph = lk['graph'].get(name, {})
        if graph.get('degree', 0) == 0 and alias != name:
            graph = lk['graph'].get(alias, {})
        deaths = lk['deaths'].get(name, []) or lk['deaths'].get(alias, [])
        profile = lk['profiles'].get(name, {}) or lk['profiles'].get(alias, {})

        # Classify
        archetype = _classify_archetype(entry, lk, name)
        emotion = _classify_emotion(entropy_val, hes, len(bugs), ver, len(deaths))
        voice = _generate_voice(name, archetype, emotion, entry, lk)

        # Display label: use archetype label as readable name
        display_name = ARCHETYPES[archetype]['label']

        # Relationships
        edges_in = graph.get('edges_in', [])
        edges_out = graph.get('edges_out', [])
        partners = profile.get('partners', [])
        fears = profile.get('fears', [])

        # Backstory from push narratives
        backstory = _extract_backstory(root, name)

        # Source code skeleton
        seq = entry.get('seq', 0)
        code_skeleton = _extract_code_skeleton(root, path, name, seq)

        # Function-level consciousness (i_am, i_want, i_give, i_fear, i_love)
        consciousness = {}
        if include_consciousness:
            fpath = root / path if path else None
            if fpath and not fpath.exists():
                parent = fpath.parent
                seq_tag = f'_s{seq:03d}_' if seq else ''
                for f in (parent.iterdir() if parent.is_dir() else []):
                    if f.suffix == '.py' and ((seq_tag and seq_tag in f.stem) or (name and name in f.stem)):
                        fpath = f
                        break
            if fpath and fpath.exists():
                try:
                    from src.觉w_fc_s019_v002_d0321_缩分话_λ18 import build_file_consciousness
                    consciousness = build_file_consciousness(fpath)
                except Exception:
                    pass

        # Memory (load BEFORE probes so probes can learn from history)
        memory = _load_memory(root, name)

        # Probe questions + self-coaching — probes read memory for self-learning
        probes = _generate_probe_questions(name, entry, lk, code_skeleton, memory)
        coaching = _generate_self_coaching(name, entry, lk, code_skeleton)

        # TODO list
        todos = _generate_todo(name, entry, lk)

        # Diagnosis from memory patterns
        diagnosis = _diagnose_patterns(name, entry, lk, memory)

        # Version history from registry
        history = entry.get('history', [])

        # Update persistent memory
        _save_memory(root, name, {
            'last_seen': datetime.now(timezone.utc).isoformat(),
            'last_bugs': bugs,
            'last_tokens': tokens,
            'last_ver': ver,
            'last_archetype': archetype,
            'last_emotion': emotion,
            'pass_count': memory.get('pass_count', 0) + 1,
            'archetype_history': (memory.get('archetype_history', []) + [archetype])[-10:],
            'emotion_history': (memory.get('emotion_history', []) + [emotion])[-10:],
            'token_history': (memory.get('token_history', []) + [tokens])[-20:],
            'bug_history': (memory.get('bug_history', []) + [bugs])[-10:],
        })

        identities.append({
            'name': name,
            'cn_name': display_name,
            'path': path,
            'archetype': archetype,
            'emotion': emotion,
            'voice': voice,
            'ver': ver,
            'tokens': tokens,
            'bugs': bugs,
            'entropy': round(entropy_val, 4),
            'entropy_data': entropy_data,
            'hesitation': round(hes, 3),
            'heat_data': heat_data,
            'desc': entry.get('desc', ''),
            'intent': entry.get('intent', ''),
            'last_change': entry.get('last_change', ''),
            'arch_emoji': ARCHETYPES[archetype]['emoji'],
            'arch_label': ARCHETYPES[archetype]['label'],
            'emo_emoji': EMOTIONS[emotion]['icon'],
            'emo_color': EMOTIONS[emotion]['color'],
            'emo_label': EMOTIONS[emotion]['label'],
            'edges_in': edges_in,
            'edges_out': edges_out,
            'partners': partners,
            'fears': fears,
            'deaths': deaths,
            'backstory': backstory,
            'code': code_skeleton,
            'probes': probes,
            'coaching': coaching,
            'todos': todos,
            'diagnosis': diagnosis,
            'history': history,
            'memory': memory,
            'dual_score': graph.get('dual_score', 0),
            'degree': graph.get('degree', 0),
            'consciousness': consciousness,
        })

    identities.sort(key=lambda x: (
        -len(x['bugs']), -x['entropy'], -x['ver'], -x['hesitation']
    ))
    return identities


if __name__ == '__main__':
    root = Path('.')
    ids = build_identities(root)
    print(f'{len(ids)} sentient modules profiled')
    for i in ids[:5]:
        cn = i['cn_name']
        a, e = i['archetype'], i['emotion']
        print(f"  {i['arch_emoji']} {cn}/{i['name']} ({a}/{e})")
        print(f"    voice: {i['voice'][:100]}")
        print(f"    relationships: {len(i['edges_in'])} in, {len(i['edges_out'])} out")
        print(f"    backstory: {len(i['backstory'])} fragments")
        print(f"    todos: {len(i['todos'])} | diagnosis: {len(i['diagnosis'])}")
        print()
