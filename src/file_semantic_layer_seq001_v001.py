"""File Semantic Layer — everything a file knows, thinks, and plans.

Unifies ALL per-file data into one semantic profile per module.
On every push cycle touch, if a module is not interlinked, its
context grows. Drift from operator intent triggers escalation.

Data sources merged per file:
  - push_baseline_seq001_v001: genesis snapshot, drift, voids, context growth
  - file_heat_map: touch score, entropy, brain region
  - module_memory: archetype, emotion, bug history, shards
  - interlink_state: test status, interlink progress
  - prompt_journal: which prompts triggered edits to this file
  - file_consciousness: inner voice, fears, loves per function
  - escalation_state: current escalation level
  - file_profiles: personality, partners, coupling
  - thought_completions: intent injections about this file
  - numeric_surface_seq001_v001: graph edges (who imports, who gets imported)

Two sync mechanisms:
  1. Intent insertion — thought completer predictions about each
     file get injected into its semantic profile as intent shards
  2. Prompt-file pairing — every prompt that mentions or edits a
     file is stored in its history, building a timeline of operator
     intent per module. Drift = divergence between stored intent
     and current file state.

Launch: called by push_cycle step 14 or manually:
  py -m src.file_semantic_layer_seq001_v001_seq001_v001
  py -c "from src.file_semantic_layer_seq001_v001_seq001_v001 import inspect_module; ..."
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ── telemetry:pulse ──
# EDIT_TS:   2026-04-12T19:00:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  create file semantic layer
# EDIT_AUTHOR: copilot
# EDIT_STATE: harvested
# ── /pulse ──

SEMANTIC_DB = 'logs/file_semantic_layer_seq001_v001.json'
JOURNAL_PATH = 'logs/prompt_journal.jsonl'
HEAT_MAP_PATH = 'file_heat_map.json'
MODULE_MEMORY_DIR = 'logs/module_memory'
INTERLINK_DB = 'logs/interlink_state.json'
ESCALATION_STATE = 'logs/escalation_state.json'
FILE_PROFILES = 'file_profiles.json'
NUMERIC_SURFACE = 'logs/numeric_surface_seq001_v001.json'
BASELINE_DB = 'logs/push_baseline_seq001_v001_state.json'
TC_LOG = 'logs/thought_completions.jsonl'
CONTEXT_REQUESTS = 'logs/context_requests.jsonl'


def _load_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding='utf-8'))
        except Exception:
            pass
    return {}


def _load_jsonl_tail(path: Path, n: int = 200) -> list[dict]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding='utf-8').splitlines()
        entries = []
        for line in lines[-n:]:
            if line.strip():
                try:
                    entries.append(json.loads(line))
                except Exception:
                    continue
        return entries
    except Exception:
        return []


def _load_semantic_db(root: Path) -> dict[str, Any]:
    return _load_json(root / SEMANTIC_DB)


def _save_semantic_db(root: Path, db: dict[str, Any]) -> None:
    path = root / SEMANTIC_DB
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(db, indent=2, ensure_ascii=False),
                    encoding='utf-8')


def _extract_prompt_history(root: Path, module_stem: str) -> list[dict]:
    """Find all prompts that reference this module — building per-file intent timeline."""
    entries = _load_jsonl_tail(root / JOURNAL_PATH, 500)
    relevant = []
    for e in entries:
        refs = e.get('module_refs', [])
        files = e.get('files_open', [])
        msg = e.get('msg', '')
        # match by: module_refs, files_open containing stem, or msg mentioning stem
        matched = (
            any(module_stem in r for r in refs)
            or any(module_stem in f for f in files)
            or module_stem in msg
        )
        if matched:
            relevant.append({
                'ts': e.get('ts', ''),
                'intent': e.get('intent', ''),
                'state': e.get('cognitive_state', ''),
                'msg_preview': msg[:120],
                'wpm': e.get('signals', {}).get('wpm', 0),
                'deletion_ratio': e.get('signals', {}).get('deletion_ratio', 0),
                'deleted_words': e.get('deleted_words', []),
            })
    return relevant[-20:]  # keep last 20 relevant prompts


def _extract_tc_intent(root: Path, module_stem: str) -> list[dict]:
    """Find thought completions that mention this module — injected intent."""
    entries = _load_jsonl_tail(root / TC_LOG, 200)
    relevant = []
    for e in entries:
        buf = e.get('buffer', '')
        comp = e.get('completion', '')
        final = e.get('final_text', '')
        if module_stem in buf or module_stem in comp or module_stem in final:
            relevant.append({
                'ts': e.get('ts', ''),
                'buffer': buf[:100],
                'completion': comp[:100],
                'accepted': e.get('accepted', False),
            })
    return relevant[-10:]


def _compute_intent_drift(prompt_history: list[dict],
                          current_state: dict) -> dict:
    """Measure how far the file has drifted from operator intent.

    Compares: what the operator ASKED for (prompt history intents)
    vs what the file IS (current state from baseline + heat map).

    Returns drift signal with magnitude and direction.
    """
    if not prompt_history:
        return {'magnitude': 0, 'direction': 'unknown', 'reason': 'no prompt history'}

    # intent distribution from prompts
    intents = {}
    for p in prompt_history:
        i = p.get('intent', 'unknown')
        intents[i] = intents.get(i, 0) + 1

    dominant_intent = max(intents, key=intents.get) if intents else 'unknown'
    total = sum(intents.values())

    # cognitive signal from prompts about this file
    avg_wpm = sum(p.get('wpm', 0) for p in prompt_history) / max(len(prompt_history), 1)
    avg_del = sum(p.get('deletion_ratio', 0) for p in prompt_history) / max(len(prompt_history), 1)

    # deleted words across all prompts about this file
    all_deleted = []
    for p in prompt_history:
        all_deleted.extend(p.get('deleted_words', []))

    # check for signs of desync
    heat = current_state.get('heat', 0)
    entropy = current_state.get('entropy', 0)
    voids = current_state.get('void_count', 0)

    # drift signals
    reasons = []
    magnitude = 0.0

    if entropy > 0.5:
        reasons.append(f'high entropy ({entropy:.2f})')
        magnitude += 0.3

    if voids > 5:
        reasons.append(f'{voids} semantic voids')
        magnitude += 0.2

    if avg_del > 0.3:
        reasons.append(f'high deletion rate in prompts ({avg_del:.1%})')
        magnitude += 0.2

    if dominant_intent == 'building' and heat < 0.1:
        reasons.append('operator intends building but file is cold')
        magnitude += 0.3

    if dominant_intent == 'testing' and not current_state.get('has_test', False):
        reasons.append('operator intends testing but no self-test exists')
        magnitude += 0.2

    magnitude = min(magnitude, 1.0)

    return {
        'magnitude': round(magnitude, 3),
        'direction': 'diverging' if magnitude > 0.3 else 'aligned',
        'dominant_intent': dominant_intent,
        'intent_distribution': intents,
        'avg_prompt_wpm': round(avg_wpm, 1),
        'avg_deletion_ratio': round(avg_del, 3),
        'deleted_words': all_deleted[-10:],
        'reasons': reasons,
    }


def build_semantic_profile(root: Path, module_stem: str) -> dict[str, Any]:
    """Build complete semantic profile for a single module.

    This is the FULL picture — everything the file knows, thinks, plans.
    """
    now = datetime.now(timezone.utc).isoformat()

    # ── data source loading ──────────────────────────────────
    heat_map = _load_json(root / HEAT_MAP_PATH)
    module_mem_path = root / MODULE_MEMORY_DIR / f'{module_stem}.json'
    module_mem = _load_json(module_mem_path)
    interlink = _load_json(root / INTERLINK_DB)
    escalation = _load_json(root / ESCALATION_STATE)
    profiles = _load_json(root / FILE_PROFILES)
    baseline = _load_json(root / BASELINE_DB)
    surface = _load_json(root / NUMERIC_SURFACE)

    # ── heat map data ────────────────────────────────────────
    heat = heat_map.get(module_stem, {})

    # ── interlink state ──────────────────────────────────────
    ilink = interlink.get(module_stem, {})

    # ── escalation ───────────────────────────────────────────
    esc_modules = escalation.get('modules', {})
    esc = esc_modules.get(module_stem, {})

    # ── file profile ─────────────────────────────────────────
    profile = profiles.get(module_stem, {})

    # ── baseline data ────────────────────────────────────────
    bl = baseline.get(module_stem, {})
    bl_context = bl.get('context', {})

    # ── numeric surface (graph) ──────────────────────────────
    edges_in = []
    edges_out = []
    nodes = surface.get('nodes', {})
    if isinstance(nodes, dict):
        node = nodes.get(module_stem, {})
        edges_in = node.get('edges_in', [])
        edges_out = node.get('edges_out', [])

    # ── prompt history ───────────────────────────────────────
    prompt_history = _extract_prompt_history(root, module_stem)

    # ── thought completer intent ─────────────────────────────
    tc_intent = _extract_tc_intent(root, module_stem)

    # ── current state (composite) ────────────────────────────
    current_state = {
        'heat': heat.get('heat', 0),
        'entropy': heat.get('entropy', 0),
        'edit_entropy': heat.get('copilot_edit_entropy', 0),
        'brain_region': heat.get('brain_region', 'unknown'),
        'void_count': bl.get('void_count', 0),
        'has_test': ilink.get('checks', {}).get('has_self_test', False),
    }

    # ── intent drift computation ─────────────────────────────
    intent_drift = _compute_intent_drift(prompt_history, current_state)

    # ── assemble semantic profile ────────────────────────────
    return {
        'module': module_stem,
        'assessed_at': now,

        # what it KNOWS (accumulated facts)
        'knows': {
            'exports': bl_context.get('known_exports', []),
            'imports': bl_context.get('known_imports', []),
            'archetype': module_mem.get('last_archetype', 'unknown'),
            'emotion': module_mem.get('last_emotion', 'unknown'),
            'personality': profile.get('personality', 'unknown'),
            'brain_region': current_state['brain_region'],
            'line_count': bl.get('latest', {}).get('line_count', 0),
            'token_count': module_mem.get('last_tokens', 0),
            'version': module_mem.get('last_ver', 0),
            'genesis_hash': bl.get('genesis_hash', ''),
        },

        # what it's THINKING (current state signals)
        'thinking': {
            'state': ilink.get('state', bl.get('state', 'unknown')),
            'heat': current_state['heat'],
            'entropy': current_state['entropy'],
            'edit_entropy': current_state['edit_entropy'],
            'void_count': current_state['void_count'],
            'recurring_voids': bl_context.get('recurring_voids', {}),
            'escalation_level': esc.get('level', 0),
            'bugs': module_mem.get('last_bugs', []),
            'fears': [],  # populated from file_consciousness if available
            'intent_drift': intent_drift,
        },

        # what it PLANS (future direction)
        'plans': {
            'needs_test': not current_state['has_test'],
            'needs_split': (bl.get('latest', {}).get('line_count', 0) > 200),
            'needs_docstrings': 'undocumented_function' in bl_context.get('recurring_voids', {}),
            'escalation_countdown': esc.get('countdown', None),
            'operator_intent': intent_drift.get('dominant_intent', 'unknown'),
            'tc_injections': tc_intent,
        },

        # HISTORY — what happened to this file over time
        'history': {
            'prompt_timeline': prompt_history,
            'push_count': bl_context.get('push_count', 0),
            'times_checked': ilink.get('times_checked', 0) or module_mem.get('pass_count', 0),
            'drift_history': bl_context.get('drift_history', []),
            'void_history': bl_context.get('void_history', []),
            'archetype_history': module_mem.get('archetype_history', [])[-10:],
            'emotion_history': module_mem.get('emotion_history', [])[-10:],
            'shards': (ilink.get('shards', []) + module_mem.get('shards', []))[-20:],
        },

        # RELATIONSHIPS — graph connections
        'relationships': {
            'partners': [p.get('name', '') for p in profile.get('partners', [])[:5]],
            'importers': edges_in[:10],
            'imports': edges_out[:10],
            'coupling_score': bl.get('latest', {}).get('coupling_score', 0),
        },
    }


def grow_on_push(root: Path, changed_files: list[str]) -> dict[str, Any]:
    """On every push, grow the semantic layer for touched modules.

    For each changed file:
    1. Build/update semantic profile
    2. Pair prompts to files (prompt-file timeline)
    3. Check intent drift (operator vs file state)
    4. If not interlinked: escalate for autonomous context growth
    5. Inject TC intent if available
    6. Never desync from operator intent — drift triggers alert

    Returns summary of growth actions taken.
    """
    db = _load_semantic_db(root)
    interlink = _load_json(root / INTERLINK_DB)
    escalation = _load_json(root / ESCALATION_STATE)
    actions = []
    now = datetime.now(timezone.utc).isoformat()

    for fpath in changed_files:
        filepath = root / fpath if not Path(fpath).is_absolute() else Path(fpath)
        if not filepath.exists() or filepath.suffix != '.py':
            continue
        if '__pycache__' in str(filepath) or filepath.name.startswith('_tmp_'):
            continue

        stem = filepath.stem
        profile = build_semantic_profile(root, stem)

        # ── store latest profile ─────────────────────────────
        existing = db.get(stem, {})
        profile_history = existing.get('profile_snapshots', [])
        # store a compressed snapshot for diff-over-time
        snapshot = {
            'ts': now,
            'state': profile['thinking']['state'],
            'heat': profile['thinking']['heat'],
            'entropy': profile['thinking']['entropy'],
            'voids': profile['thinking']['void_count'],
            'intent': profile['plans']['operator_intent'],
            'drift_mag': profile['thinking']['intent_drift']['magnitude'],
            'exports_n': len(profile['knows']['exports']),
            'prompt_count': len(profile['history']['prompt_timeline']),
        }
        profile_history.append(snapshot)
        if len(profile_history) > 30:
            profile_history = profile_history[-30:]

        db[stem] = {
            'latest': profile,
            'profile_snapshots': profile_history,
            'first_seen': existing.get('first_seen', now),
            'last_updated': now,
        }

        # ── decision: escalate or sleep ──────────────────────
        ilink_state = interlink.get(stem, {}).get('state', 'baseline')
        drift_mag = profile['thinking']['intent_drift']['magnitude']

        action = {'module': stem, 'ts': now}

        if ilink_state in ('interlinked', 'sleeping'):
            # interlinked — no growth needed, just snapshot
            action['action'] = 'snapshot_only'
            action['reason'] = f'interlinked — stable'
        elif drift_mag > 0.5:
            # high intent drift — escalate for operator attention
            action['action'] = 'escalate_drift'
            action['reason'] = profile['thinking']['intent_drift'].get('reasons', [])
            action['drift'] = drift_mag
            _escalate_for_context(root, stem, escalation, profile)
        elif profile['thinking']['void_count'] > 5:
            # many voids — needs autonomous context growth
            action['action'] = 'grow_context'
            action['reason'] = f'{profile["thinking"]["void_count"]} semantic voids'
            _request_autonomous_growth(root, stem, profile)
        else:
            action['action'] = 'grow_passive'
            action['reason'] = 'standard push growth'

        actions.append(action)

    _save_semantic_db(root, db)
    return {
        'modules_processed': len(actions),
        'actions': actions,
        'escalated': sum(1 for a in actions if a['action'] == 'escalate_drift'),
        'growing': sum(1 for a in actions if a['action'] == 'grow_context'),
    }


def _escalate_for_context(root: Path, stem: str,
                          escalation: dict, profile: dict) -> None:
    """Escalate a module that has drifted from operator intent."""
    modules = escalation.get('modules', {})
    entry = modules.get(stem, {})
    entry['level'] = max(entry.get('level', 0), 2)
    entry['drift_escalation'] = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'magnitude': profile['thinking']['intent_drift']['magnitude'],
        'reasons': profile['thinking']['intent_drift'].get('reasons', []),
        'dominant_intent': profile['plans']['operator_intent'],
    }
    modules[stem] = entry
    escalation['modules'] = modules
    path = root / ESCALATION_STATE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(escalation, indent=2, ensure_ascii=False),
                    encoding='utf-8')


def _request_autonomous_growth(root: Path, stem: str,
                               profile: dict) -> None:
    """File a request for autonomous context growth.

    The module is asking: 'I have voids in my self-understanding.
    Fill them on the next cycle without operator intervention.'
    """
    path = root / CONTEXT_REQUESTS
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'module': stem,
        'type': 'autonomous_growth',
        'void_count': profile['thinking']['void_count'],
        'recurring_voids': profile['thinking']['recurring_voids'],
        'current_state': profile['thinking']['state'],
        'operator_intent': profile['plans']['operator_intent'],
        'prompt_count': len(profile['history']['prompt_timeline']),
    }
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry) + '\n')


def inspect_module(root: Path, module_stem: str) -> str:
    """Human-readable inspection of a module's semantic layer."""
    p = build_semantic_profile(root, module_stem)
    lines = [f'═══ {module_stem} ═══', '']

    # KNOWS
    lines.append('▸ KNOWS')
    lines.append(f'  archetype: {p["knows"]["archetype"]} | '
                 f'emotion: {p["knows"]["emotion"]} | '
                 f'personality: {p["knows"]["personality"]}')
    lines.append(f'  region: {p["knows"]["brain_region"]} | '
                 f'v{p["knows"]["version"]} | '
                 f'{p["knows"]["line_count"]} lines | '
                 f'{p["knows"]["token_count"]} tokens')
    lines.append(f'  exports: {", ".join(p["knows"]["exports"][:5]) or "none"}')
    lines.append(f'  imports: {len(p["knows"]["imports"])} modules')
    lines.append('')

    # THINKING
    t = p['thinking']
    lines.append('▸ THINKING')
    lines.append(f'  state: {t["state"]} | heat: {t["heat"]:.2f} | '
                 f'entropy: {t["entropy"]:.2f}')
    lines.append(f'  voids: {t["void_count"]} | '
                 f'escalation: L{t["escalation_level"]}')
    if t['recurring_voids']:
        top = sorted(t['recurring_voids'].items(), key=lambda x: -x[1])[:3]
        lines.append(f'  recurring: {", ".join(f"{k}({v})" for k,v in top)}')
    drift = t['intent_drift']
    lines.append(f'  intent drift: {drift["magnitude"]:.2f} '
                 f'({drift["direction"]})')
    if drift.get('reasons'):
        for r in drift['reasons'][:3]:
            lines.append(f'    ⚠ {r}')
    lines.append('')

    # PLANS
    pl = p['plans']
    lines.append('▸ PLANS')
    needs = []
    if pl['needs_test']:
        needs.append('test')
    if pl['needs_split']:
        needs.append('split')
    if pl['needs_docstrings']:
        needs.append('docstrings')
    lines.append(f'  needs: {", ".join(needs) or "nothing"}')
    lines.append(f'  operator intent: {pl["operator_intent"]}')
    if pl['tc_injections']:
        lines.append(f'  TC injections: {len(pl["tc_injections"])}')
    lines.append('')

    # HISTORY
    h = p['history']
    lines.append('▸ HISTORY')
    lines.append(f'  {h["push_count"]} pushes | '
                 f'{h["times_checked"]} checks | '
                 f'{len(h["prompt_timeline"])} prompts | '
                 f'{len(h["shards"])} shards')
    if h['prompt_timeline']:
        last = h['prompt_timeline'][-1]
        lines.append(f'  last prompt: [{last["intent"]}] '
                     f'{last["msg_preview"][:60]}...')
    lines.append('')

    # RELATIONSHIPS
    r = p['relationships']
    lines.append('▸ RELATIONSHIPS')
    lines.append(f'  coupling: {r["coupling_score"]} | '
                 f'{len(r["importers"])} importers | '
                 f'{len(r["imports"])} imports')
    if r['partners']:
        lines.append(f'  partners: {", ".join(r["partners"][:3])}')

    return '\n'.join(lines)


def build_semantic_report(root: Path) -> str:
    """Build markdown report for prompt injection — compact summary of all profiled modules."""
    db = _load_semantic_db(root)
    if not db:
        return ''

    lines = ['<!-- pigeon:semantic-layer -->', '## File Semantic Layer', '']
    lines.append(f'*{len(db)} modules profiled*')
    lines.append('')

    # sort by drift magnitude descending
    ranked = []
    for stem, entry in db.items():
        latest = entry.get('latest', {})
        drift = latest.get('thinking', {}).get('intent_drift', {}).get('magnitude', 0)
        voids = latest.get('thinking', {}).get('void_count', 0)
        state = latest.get('thinking', {}).get('state', '?')
        prompts = len(latest.get('history', {}).get('prompt_timeline', []))
        ranked.append((stem, drift, voids, state, prompts))

    ranked.sort(key=lambda x: (-x[1], -x[2]))

    # drifted modules
    drifted = [r for r in ranked if r[1] > 0.3]
    if drifted:
        lines.append('**Intent-drifted (operator intent ≠ file state):**')
        for stem, drift, voids, state, prompts in drifted[:8]:
            lines.append(f'- `{stem}`: drift={drift:.2f} voids={voids} '
                         f'state={state} prompts={prompts}')
        lines.append('')

    # context-hungry modules
    hungry = [r for r in ranked if r[2] > 5 and r[1] <= 0.3]
    if hungry:
        lines.append('**Context-hungry (growing, many voids):**')
        for stem, drift, voids, state, prompts in hungry[:5]:
            lines.append(f'- `{stem}`: {voids} voids, {prompts} prompts')
        lines.append('')

    # prompt-rich but cold (operator talks about it but it doesn't change)
    cold = [r for r in ranked if r[4] > 3 and r[1] <= 0.1]
    if cold:
        lines.append('**Talked-about but cold (operator references, no drift):**')
        for stem, drift, voids, state, prompts in cold[:5]:
            lines.append(f'- `{stem}`: {prompts} prompts, state={state}')
        lines.append('')

    lines.append('<!-- /pigeon:semantic-layer -->')
    return '\n'.join(lines)


if __name__ == '__main__':
    root = Path(__file__).resolve().parent.parent
    # manual inspection
    import sys
    if len(sys.argv) > 1:
        mod = sys.argv[1]
        print(inspect_module(root, mod))
    else:
        # run on a few known modules
        for stem in ['interlinker_seq001_v001', 'push_baseline_seq001_v001', 'escalation_engine_seq001_v001']:
            print(inspect_module(root, stem))
            print()
