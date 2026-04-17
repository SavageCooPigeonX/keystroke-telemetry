"""module_identity_orchestrator_seq014_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 014 | VER: v001 | 155 lines | ~1,549 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
import ast
import re

from .module_identity_sources_seq004_v001 import _load_all_sources
from .module_identity_alias_seq003_v001 import _build_alias_map
from .module_identity_lookups_seq005_v001 import _build_lookups
from .module_identity_classify_seq010_v001 import _classify_archetype, _classify_emotion
from .module_identity_voice_seq011_v001 import _generate_voice
from .module_identity_backstory_seq006_v001 import _extract_backstory
from .module_identity_code_seq007_v001.module_identity_code_seq007_v001_wrapper_seq004_v001 import _extract_code_skeleton
from .module_identity_utils_seq002_v001 import _load_memory, _save_memory
from .module_identity_probes_seq008_v001 import _generate_probe_questions
from .module_identity_coaching_seq009_v001 import _generate_self_coaching
from .module_identity_todo_seq012_v001 import _generate_todo
from .module_identity_diagnose_seq013_v001 import _diagnose_patterns
from .module_identity_constants_seq001_v001 import ARCHETYPES, EMOTIONS

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

        # Memory (load BEFORE voice so voice can reference history arc)
        memory = _load_memory(root, name)

        # Backstory from push narratives (also needed by voice)
        backstory = _extract_backstory(root, name)

        # Source code skeleton
        seq = entry.get('seq', 0)
        code_skeleton = _extract_code_skeleton(root, path, name, seq)

        # Voice — passes memory + backstory for rich narrative arc
        voice = _generate_voice(name, archetype, emotion, entry, lk,
                                memory=memory, backstory=backstory)

        # Display label: use archetype label as readable name
        display_name = ARCHETYPES[archetype]['label']

        # Relationships
        edges_in = graph.get('edges_in', [])
        edges_out = graph.get('edges_out', [])
        partners = profile.get('partners', [])
        fears = profile.get('fears', [])

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
