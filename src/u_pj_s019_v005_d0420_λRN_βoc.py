"""Enriched prompt journal — every entry cross-references all telemetry.

Replaces the dumb 4-field journal with a full telemetry snapshot per prompt.
Each entry captures: cognitive state, typing signals, deleted words, active
tasks, module heat, session running stats, and intent classification.

Designed for live analysis: grep any field, plot any metric, no aggregation needed.
Zero LLM calls — pure signal cross-referencing.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 019 | VER: v005 | 999 lines | ~9,863 tokens
# DESC:   every_entry_cross_references_all
# INTENT: chore_pigeon_rename_cascade
# LAST:   2026-04-20 @ c61fc91
# SESSIONS: 3
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

JOURNAL_PATH   = 'logs/prompt_journal.jsonl'
SNAPSHOT_PATH  = 'logs/prompt_telemetry_latest.json'
COMPS_PATH     = 'logs/chat_compositions.jsonl'
PROMPT_COMPS_PATH = 'logs/prompt_compositions.jsonl'
HEAT_PATH      = 'file_heat_map.json'
TASK_PATH      = 'task_queue.json'
PROFILE_PATH   = 'operator_profile.md'
EDIT_PAIRS     = 'logs/edit_pairs.jsonl'
MUTATIONS_PATH = 'logs/copilot_prompt_mutations.json'
COPILOT_PATH   = '.github/copilot-instructions.md'
MAX_COMP_AGE_MS = 120_000    # 2min window — compositions may lag behind prompt submission
TIGHT_WINDOW_MS = 500        # ±500ms for high-confidence direct binding
MIN_TEXT_MATCH_SCORE = 0.4   # lowered: partial prompt text often matches loosely

PROMPT_BLOCK_START = '<!-- pigeon:prompt-telemetry -->'
PROMPT_BLOCK_END = '<!-- /pigeon:prompt-telemetry -->'
TASK_COMPLETE_HOOK_MARKERS = (
    'you were about to complete but a hook blocked you with the following message',
    'you have not yet marked the task as complete using the task_complete tool',
)

# Intent keywords → category
INTENT_MAP = {
    'fix':       'debugging',  'bug':     'debugging',  'error':  'debugging',
    'broke':     'debugging',  'wrong':   'debugging',  'fail':   'debugging',
    'implement': 'building',   'build':   'building',   'create': 'building',
    'add':       'building',   'wire':    'building',   'make':   'building',
    'refactor':  'restructuring', 'split': 'restructuring', 'rename': 'restructuring',
    'move':      'restructuring', 'clean': 'restructuring',
    'test':      'testing',    'run':     'testing',    'verify': 'testing',
    'what':      'exploring',  'how':     'exploring',  'why':    'exploring',
    'show':      'exploring',  'find':    'exploring',  'check':  'exploring',
    'push':      'shipping',   'commit':  'shipping',   'deploy': 'shipping',
    'update':    'documenting','readme':  'documenting','doc':    'documenting',
    'continu':   'continuing',
}


def _classify_intent(msg: str) -> str:
    """Classify prompt intent from first matching keyword."""
    low = msg.lower()
    for kw, cat in INTENT_MAP.items():
        if kw in low:
            return cat
    return 'unknown'


def _is_meta_hook_message(msg: str) -> bool:
    low = msg.lower()
    return all(marker in low for marker in TASK_COMPLETE_HOOK_MARKERS)


def _is_operator_entry(entry: dict) -> bool:
    if entry.get('prompt_kind') == 'meta_hook':
        return False
    return not _is_meta_hook_message(str(entry.get('msg', '')))


def _build_meta_hook_entry(
    root: Path,
    now: datetime,
    msg: str,
    files_open: list[str],
    session_n: int,
    meta_prompt_kind: str,
) -> dict:
    return {
        'ts':               now.isoformat(),
        'session_n':        session_n,
        'msg':              msg,
        'msg_len':          len(msg),
        'files_open':       files_open,
        'prompt_kind':      'meta_hook',
        'intent':           'meta',
        'module_refs':      [],
        'cognitive_state':  'unknown',
        'signals':          {},
        'composition_binding': {
            'matched': False,
            'source': None,
            'age_ms': None,
            'key': None,
        },
        'deleted_words':    [],
        'rewrites':         [],
        'task_queue':       _active_tasks(root),
        'hot_modules':      _hot_modules(root),
        'prompt_mutations': _mutation_count(root),
        'running':          _running_stats(root),
        'provenance': {
            'measured': ['ts', 'session_n', 'msg', 'msg_len', 'files_open',
                         'signals', 'deleted_words', 'rewrites', 'composition_binding'],
            'derived':  ['intent', 'module_refs', 'cognitive_state',
                         'task_queue', 'hot_modules', 'prompt_mutations', 'running'],
        },
        'meta_prompt_kind': meta_prompt_kind,
    }


def _extract_module_refs(msg: str) -> list[str]:
    """Pull module names mentioned in the prompt text."""
    # Match pigeon module patterns and common module references
    refs = re.findall(r'\b(\w+_seq\d+)\b', msg)
    # Also catch short names from the module map
    short = re.findall(r'\b(dynamic_prompt|task_queue|operator_stats|file_heat|'
                       r'self_fix|push_narrative|cognitive_reactor|pulse_harvest|'
                       r'query_memory|rework_detector|drift_watcher|resistance_bridge|'
                       r'context_budget|streaming_layer|os_hook|git_plugin|'
                       r'prompt_journal|logger|models|timestamp)\b', msg, re.I)
    return list(set(refs + [s.lower() for s in short]))


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        entries = []
        with open(path, encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        return entries
    except Exception:
        return []


def _should_skip_duplicate_meta_prompt(root: Path, msg: str, meta_prompt_kind: str | None) -> bool:
    if not meta_prompt_kind:
        return False
    entries = _read_jsonl(root / JOURNAL_PATH)
    if not entries:
        return False
    last = entries[-1]
    if last.get('msg') != msg:
        return False
    if last.get('meta_prompt_kind') == meta_prompt_kind:
        return True
    return _is_meta_hook_message(str(last.get('msg', '')))


def _parse_timestamp_ms(value) -> int | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.isdigit():
            return int(text)
        try:
            dt = datetime.fromisoformat(text.replace('Z', '+00:00'))
            return int(dt.timestamp() * 1000)
        except ValueError:
            return None
    return None


def _composition_key(comp: dict) -> str:
    parts = [
        str(comp.get('event_hash', '')),
        str(comp.get('first_key_ts', '')),
        str(comp.get('last_key_ts', '')),
        str(comp.get('ts', '')),
        str(comp.get('total_keystrokes', '')),
        str(comp.get('duration_ms', '')),
        str(comp.get('final_text', ''))[:120],
    ]
    return '|'.join(parts)


def _dedup_uia_chars(value: str) -> str:
    """Collapse UIA poll-artifact char tripling: 'fffrroroomm' -> 'from'.
    Uses aggressive consecutive-run collapse + a second pass to handle
    interleaved artifacts like 'frorom' -> 'from'.
    """
    # Pass 1: collapse consecutive runs (fff -> f, rr -> r, oo -> o)
    value = re.sub(r'(.)\1{1,}', r'\1', value)
    value = re.sub(r'\s+', ' ', value).strip()
    return value


def _token_set_uia(value: str) -> set[str]:
    """Token set that also deduplicates UIA char artifacts within each token."""
    tokens = re.findall(r'[a-z0-9]+', value.lower())
    result = set()
    for t in tokens:
        deduped = re.sub(r'(.)\1{1,}', r'\1', t)
        result.add(deduped)
    return result


def _normalize_prompt_text(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r'\s+', ' ', value)
    return value


def _normalize_comp_text(value: str) -> str:
    """Normalize composition text — also strips UIA tripling artifacts."""
    value = value.lower().strip()
    value = _dedup_uia_chars(value)
    return value


def _token_set(value: str) -> set[str]:
    return {token for token in re.findall(r'[a-z0-9]+', value.lower()) if token}


def _text_match_score(msg: str, comp: dict) -> float:
    msg_norm = _normalize_prompt_text(msg)
    if not msg_norm:
        return 0.0

    comp_text = comp.get('final_text') or comp.get('peak_buffer') or ''
    comp_norm = _normalize_comp_text(comp_text)
    if not comp_norm:
        return 0.0

    if msg_norm == comp_norm:
        return 1.0

    msg_tokens = _token_set(msg_norm)
    comp_tokens = _token_set_uia(comp_norm)  # UIA-aware dedup on comp side
    if not msg_tokens or not comp_tokens:
        return 0.0

    overlap = len(msg_tokens & comp_tokens) / max(len(msg_tokens | comp_tokens), 1)

    if len(msg_norm) <= 24 or len(msg_tokens) <= 3:
        return overlap

    containment = 1.0 if msg_norm in comp_norm or comp_norm in msg_norm else 0.0
    return max(overlap, containment)


def _recent_bound_composition_keys(root: Path, limit: int = 8) -> set[str]:
    entries = _read_jsonl(root / JOURNAL_PATH)
    keys = set()
    for entry in entries[-limit:]:
        binding = entry.get('composition_binding', {})
        key = binding.get('key')
        if key:
            keys.add(key)
    return keys


def _recent_bound_session_ns(root: Path, limit: int = 8) -> set[int]:
    """Return session_n values already used for composition binding."""
    entries = _read_jsonl(root / JOURNAL_PATH)
    ns: set[int] = set()
    for entry in entries[-limit:]:
        sn = entry.get('session_n')
        if sn is not None:
            ns.add(sn)
    return ns


def _candidate_compositions(root: Path, now_ms: int, msg: str) -> list[dict]:
    candidates = []
    sources = [
        ('prompt_compositions', root / PROMPT_COMPS_PATH),
        ('chat_compositions', root / COMPS_PATH),
    ]
    for source, path in sources:
        for entry in _read_jsonl(path):
            comp_ts = (
                _parse_timestamp_ms(entry.get('last_key_ts'))
                or _parse_timestamp_ms(entry.get('first_key_ts'))
                or _parse_timestamp_ms(entry.get('ts'))
            )
            if comp_ts is None or comp_ts > now_ms:
                continue
            candidates.append({
                'source': source,
                'entry': entry,
                'ts_ms': comp_ts,
                'age_ms': now_ms - comp_ts,
                'key': _composition_key(entry),
                'match_score': _text_match_score(msg, entry),
            })
    candidates.sort(
        key=lambda item: (-item['match_score'], item['age_ms'], 0 if item['source'] == 'prompt_compositions' else 1)
    )
    return candidates


def _select_composition(root: Path, now: datetime, msg: str,
                        session_n: int | None = None) -> dict | None:
    now_ms = int(now.timestamp() * 1000)
    used_keys = _recent_bound_composition_keys(root)
    candidates = _candidate_compositions(root, now_ms, msg)
    for candidate in candidates:
        age = candidate['age_ms']
        score = candidate['match_score']
        # Perfect text match — this IS the right composition, bypass age filter
        if score >= 0.95 and candidate['key'] not in used_keys:
            return candidate
        if age > MAX_COMP_AGE_MS:
            continue
        if score < MIN_TEXT_MATCH_SCORE:
            # UIA-tripled text often fails text matching — accept by time if
            # the composition text looks like a tripled artifact (char runs >= 2x)
            comp_text = candidate.get('entry', {}).get('final_text', '')
            run_ratio = len(re.findall(r'(.)\1', comp_text)) / max(len(comp_text), 1)
            if run_ratio < 0.15:  # not UIA-tripled — genuinely bad match
                continue
        if candidate['key'] in used_keys:
            continue
        # ±500ms tight-window override: if the composition was created within
        # 500ms of the journal entry AND score is high, accept unconditionally.
        if age <= TIGHT_WINDOW_MS and score >= 0.8:
            return candidate
        # For looser matches, enforce session_n uniqueness as secondary gate
        # to prevent same-session stale composition from contaminating entries.
        comp_entry = candidate.get('entry', {})
        comp_sn = comp_entry.get('session_n')
        if comp_sn is not None and session_n is not None and comp_sn == session_n - 1:
            # Composition is from the previous session item — valid
            return candidate
        if comp_sn is not None and comp_sn == session_n:
            return candidate
        # No session_n info on the composition — fall through to age check
        if age <= MAX_COMP_AGE_MS:
            return candidate
    return None


def _refresh_prompt_compositions(root: Path) -> None:
    try:
        import importlib.util

        prompt_recon_path = root / 'src' / 'prompt_recon_seq016_v001.py'
        if not prompt_recon_path.exists():
            return

        spec = importlib.util.spec_from_file_location('_prompt_recon_runtime', prompt_recon_path)
        if spec is None or spec.loader is None:
            return

        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        reconstruct_latest = getattr(mod, 'reconstruct_latest', None)
        if callable(reconstruct_latest):
            reconstruct_latest(root)
    except Exception:
        return


def _load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text('utf-8'))
    except Exception:
        return None


def _active_tasks(root: Path) -> dict:
    """Summarize task queue state."""
    data = _load_json(root / TASK_PATH)
    if not data:
        return {'total': 0, 'in_progress': [], 'pending': 0}
    tasks = data if isinstance(data, list) else data.get('tasks', [])
    ip = [t.get('id', '?') for t in tasks if t.get('status') == 'in_progress']
    pending = sum(1 for t in tasks if t.get('status') == 'pending')
    done = sum(1 for t in tasks if t.get('status') == 'done')
    return {'total': len(tasks), 'in_progress': ip, 'pending': pending, 'done': done}


def _hot_modules(root: Path, top_n: int = 3) -> list[dict]:
    """Top N modules by hesitation from heat map."""
    data = _load_json(root / HEAT_PATH)
    if not data or not isinstance(data, dict):
        return []
    ranked = sorted(
        ((name, d.get('avg_hes', 0)) for name, d in data.items()
         if isinstance(d, dict) and d.get('total', 0) >= 2),
        key=lambda x: x[1], reverse=True
    )
    return [{'module': n, 'hes': round(h, 3)} for n, h in ranked[:top_n]]


def _running_stats(root: Path) -> dict:
    """Compute running session stats from existing journal entries + baselines."""
    p = root / JOURNAL_PATH
    if not p.exists():
        return {}
    try:
        entries = [json.loads(l) for l in open(p, encoding='utf-8') if l.strip()]
    except Exception:
        return {}
    entries = [entry for entry in entries if _is_operator_entry(entry)]
    if not entries:
        return {}
    n = len(entries)
    # Running averages from entries that have signals
    wpms = [e['signals']['wpm'] for e in entries
             if 'signals' in e and 'wpm' in e.get('signals', {})
             and e['signals']['wpm'] <= 300]
    dels = [
        e['signals']['deletion_ratio']
        for e in entries
        if isinstance(e.get('signals'), dict) and 'deletion_ratio' in e['signals']
    ]
    # Load real state distribution + baselines from operator_profile.md
    # (prompt_journal entries never receive classify results, so their
    #  cognitive_state is always '?' / 'unknown' — useless for stats)
    state_dist = {}
    dominant_state = 'unknown'
    baselines = {}
    try:
        import importlib.util
        matches = sorted(root.glob('src/控w_ops_s008*.py'))
        if matches:
            spec = importlib.util.spec_from_file_location('_os', matches[-1])
            if spec and spec.loader:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                op_path = root / 'operator_profile.md'
                if op_path.exists():
                    stats = mod.OperatorStats(str(op_path))
                    baselines = mod.compute_baselines(stats._history)
                    from collections import Counter
                    real_states = [r['state'] for r in stats._history if 'state' in r]
                    state_dist = dict(Counter(real_states).most_common(5))
                    if state_dist:
                        dominant_state = max(state_dist, key=state_dist.get)
    except Exception:
        pass

    # Fallback: if operator_profile gave nothing, count from journal entries
    if not state_dist:
        from collections import Counter
        states = [e.get('cognitive_state', 'unknown') for e in entries]
        state_dist = dict(Counter(states).most_common(5))

    return {
        'total_prompts': n,
        'avg_wpm':       round(sum(wpms) / len(wpms), 1) if wpms else None,
        'avg_del_ratio': round(sum(dels) / len(dels), 3) if dels else None,
        'dominant_state': dominant_state,
        'state_distribution': state_dist,
        'baselines': baselines if baselines else None,
    }


def _mutation_count(root: Path) -> int:
    data = _load_json(root / MUTATIONS_PATH)
    if not data:
        return 0
    if isinstance(data, list):
        return len(data)
    return len(data.get('snapshots', []))


def _trim_text(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return value[: max(limit - 3, 0)] + '...'


def _dominant_state(state_dist: dict) -> str | None:
    if not state_dist:
        return None
    return next(iter(state_dist))


def _predict_next_issues(root: Path, current_intent: str, current_refs: list[str]) -> list[dict]:
    """Analyze prompt journal history to predict what the operator will debug next.

    Pattern mining:
    1. After frustrated/hesitant states, which modules come up in the NEXT 3 prompts?
    2. Recurring module→debug cycles (touched module X → debugged X within 5 prompts)
    3. Modules with high heat + recent mention = likely next struggle
    """
    entries = _read_jsonl(root / JOURNAL_PATH)
    entries = [entry for entry in entries if _is_operator_entry(entry)]
    if len(entries) < 10:
        return []

    from collections import Counter
    # Pattern 1: modules that follow frustrated states
    post_frustration_modules: Counter = Counter()
    for i, e in enumerate(entries):
        if e.get('cognitive_state') in ('frustrated', 'hesitant'):
            for j in range(i + 1, min(i + 4, len(entries))):
                for ref in entries[j].get('module_refs', []):
                    post_frustration_modules[ref] += 1

    # Pattern 2: debug cycles — implement/build → debug same module
    debug_cycles: Counter = Counter()
    for i, e in enumerate(entries):
        if e.get('intent') in ('building', 'restructuring'):
            refs = set(e.get('module_refs', []))
            for j in range(i + 1, min(i + 6, len(entries))):
                if entries[j].get('intent') == 'debugging':
                    for ref in entries[j].get('module_refs', []):
                        if ref in refs:
                            debug_cycles[ref] += 1

    # Pattern 3: recent module mentions trending toward frustration
    recent = entries[-15:]
    recent_refs: Counter = Counter()
    for e in recent:
        weight = 2 if e.get('cognitive_state') in ('frustrated', 'hesitant') else 1
        for ref in e.get('module_refs', []):
            recent_refs[ref] += weight

    # Merge signals — score each module
    all_modules = set(post_frustration_modules) | set(debug_cycles) | set(recent_refs)
    predictions = []
    heat = {m['module']: m['hes'] for m in _hot_modules(root, top_n=20)}
    for mod in all_modules:
        score = (
            post_frustration_modules.get(mod, 0) * 0.3 +
            debug_cycles.get(mod, 0) * 0.5 +
            recent_refs.get(mod, 0) * 0.2 +
            heat.get(mod, 0) * 2.0
        )
        if score >= 1.0:
            reasons = []
            if debug_cycles.get(mod, 0) >= 2:
                reasons.append(f'{debug_cycles[mod]}x build→debug cycle')
            if post_frustration_modules.get(mod, 0) >= 2:
                reasons.append(f'follows frustration {post_frustration_modules[mod]}x')
            if heat.get(mod, 0) >= 0.5:
                reasons.append(f'high heat ({heat[mod]:.2f})')
            if recent_refs.get(mod, 0) >= 3:
                reasons.append('trending in recent prompts')
            predictions.append({'module': mod, 'score': round(score, 2), 'reasons': reasons})

    predictions.sort(key=lambda p: p['score'], reverse=True)
    return predictions[:4]


def _load_fresh_coaching_bullets(root: Path, max_age_s: float = 7200.0) -> list[str]:
    """Read coaching bullet lines from operator_coaching.md if < max_age_s old."""
    coaching_path = root / 'operator_coaching.md'
    if not coaching_path.exists():
        return []
    try:
        import time as _time
        if _time.time() - coaching_path.stat().st_mtime > max_age_s:
            return []
        text = coaching_path.read_text(encoding='utf-8')
        # Pull bullet lines (- **...**) from coaching block or plain markdown
        bullets = re.findall(r'^\s*[-*]\s+\*\*(.+?)\*\*', text, re.MULTILINE)
        if not bullets:
            bullets = re.findall(r'^\s*[-*]\s+(.+)', text, re.MULTILINE)
        return [b.strip() for b in bullets[:6]]
    except Exception:
        return []


def _build_snapshot(entry: dict) -> dict:
    running = entry.get('running', {})
    state_dist = running.get('state_distribution', {})
    rewrites = entry.get('rewrites', [])

    # Load fresh coaching directives from operator_coaching.md (< 2h old)
    root = entry.get('_root')
    coaching_bullets: list[str] = []
    if root:
        try:
            coaching_bullets = _load_fresh_coaching_bullets(root)
        except Exception:
            pass

    snapshot = {
        'schema': 'prompt_telemetry/latest/v1',
        'updated_at': entry['ts'],
        'latest_prompt': {
            'session_n': entry['session_n'],
            'ts': entry['ts'],
            'chars': entry['msg_len'],
            'preview': _trim_text(entry['msg'], 220),
            'intent': entry['intent'],
            'state': entry['cognitive_state'],
            'files_open': entry.get('files_open', [])[:6],
            'module_refs': sorted(entry.get('module_refs', []))[:8],
        },
        'signals': entry.get('signals', {}),
        'composition_binding': entry.get('composition_binding', {}),
        'deleted_words': entry.get('deleted_words', [])[:8],
        'rewrites': [
            {
                'old': _trim_text(str(r.get('old', '')), 80),
                'new': _trim_text(str(r.get('new', '')), 80),
            }
            for r in rewrites[:3]
        ],
        'task_queue': entry.get('task_queue', {}),
        'hot_modules': entry.get('hot_modules', []),
        'running_summary': {
            'total_prompts': running.get('total_prompts'),
            'avg_wpm': running.get('avg_wpm'),
            'avg_del_ratio': running.get('avg_del_ratio'),
            'dominant_state': _dominant_state(state_dist),
            'state_distribution': state_dist,
            'baselines': running.get('baselines'),
        },
    }
    if coaching_bullets:
        snapshot['coaching_directives'] = coaching_bullets

    # Predictive debug — surface likely next struggles
    if root:
        try:
            preds = _predict_next_issues(
                root, entry.get('intent', ''), entry.get('module_refs', []))
            if preds:
                snapshot['predicted_struggles'] = preds
        except Exception:
            pass

    return snapshot


def _write_latest_snapshot(root: Path, snapshot: dict) -> None:
    snapshot_path = root / SNAPSHOT_PATH
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def _latest_runtime_module(root: Path, pattern: str) -> Path | None:
    matches = sorted(root.glob(pattern))
    return matches[-1] if matches else None


def _refresh_copilot_instructions(root: Path, snapshot: dict) -> None:
    try:
        import importlib.util

        manager_path = _latest_runtime_module(root, 'src/管w_cpm_s020*.py')
        if manager_path is not None:
            spec = importlib.util.spec_from_file_location('_copilot_prompt_manager_runtime', manager_path)
            if spec is not None and spec.loader is not None:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                refresh = getattr(mod, 'refresh_managed_prompt', None)
                if callable(refresh):
                    refresh(root, snapshot=snapshot, track_mutations=False)
                    return
    except Exception:
        pass

    cp_path = root / COPILOT_PATH
    if not cp_path.exists():
        return

    text = cp_path.read_text(encoding='utf-8')
    pattern = re.compile(
        rf'{re.escape(PROMPT_BLOCK_START)}[\s\S]*?{re.escape(PROMPT_BLOCK_END)}',
        re.DOTALL,
    )
    block = (
        f'{PROMPT_BLOCK_START}\n'
        '## Live Prompt Telemetry\n\n'
        f'*Auto-updated per prompt · source: `{SNAPSHOT_PATH}`*\n\n'
        'Use this block as the highest-freshness prompt-level telemetry. '
        'When it conflicts with older commit-time context, prefer this block.\n\n'
        '```json\n'
        f'{json.dumps(snapshot, ensure_ascii=False, indent=2)}\n'
        '```\n\n'
        f'{PROMPT_BLOCK_END}'
    )
    text_without_block = pattern.sub('', text).rstrip() + '\n'
    anchor = '<!-- /pigeon:operator-state -->'
    if anchor in text_without_block:
        new_text = text_without_block.replace(anchor, anchor + '\n\n' + block, 1)
    else:
        new_text = text_without_block.rstrip() + '\n\n' + block + '\n'

    if new_text != text:
        cp_path.write_text(new_text, encoding='utf-8')


def _write_self_composition(root: Path, msg: str, now: datetime) -> None:
    """Write a minimal self-composition entry so binding always finds a match.

    Called when vscdb_poller (or any auto-caller) has the exact submitted text
    but UIA is not running — prevents matched=False for all non-UIA sessions.
    """
    comp_path = root / 'logs' / 'chat_compositions.jsonl'
    comp_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        'ts': now.isoformat(),
        'final_text': msg,
        'source': 'vscdb_self',
        'chat_state': {'state': 'unknown', 'confidence': 1.0, 'signals': {}},
        'deleted_words': [],
        'intent_deleted_words': [],
        'rewrites': [],
        'hesitation_windows': [],
        'deletion_ratio': 0.0,
        'intent_deletion_ratio': 0.0,
        'peak_buffer': msg,
        'duration_ms': 0,
    }
    with open(comp_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def _force_fresh_composition(root: Path) -> None:
    """Force a fresh composition analysis from raw keystrokes before binding.

    This ensures the CURRENT prompt's deleted words are available for binding,
    rather than waiting for the classify_bridge flush timer (~60s).
    """
    try:
        import importlib.util
        analyzer_path = root / 'client' / 'chat_composition_analyzer_seq001_v001.py'
        if not analyzer_path.exists():
            return
        spec = importlib.util.spec_from_file_location('_comp_analyzer', analyzer_path)
        if spec is None or spec.loader is None:
            return
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        fn = getattr(mod, 'analyze_and_log', None)
        if callable(fn):
            fn(root)
    except Exception:
        pass


def log_enriched_entry(root: Path, msg: str, files_open: list[str],
                       session_n: int) -> dict:
    """Build and append one fully-enriched journal entry. Returns the entry.

    Signal/narrative separation:
    1. Write raw measured signal to prompt_signal_raw.jsonl (ground truth)
    2. Build enriched entry with interpretation (intent, state, predictions)
    3. Enriched entry is tagged with provenance markers
    """
    now = datetime.now(timezone.utc)
    meta_prompt_kind = 'task_complete_hook' if _is_meta_hook_message(msg) else None
    if meta_prompt_kind:
        entry = _build_meta_hook_entry(root, now, msg, files_open, session_n, meta_prompt_kind)
        if _should_skip_duplicate_meta_prompt(root, msg, meta_prompt_kind):
            return entry
        journal_path = root / JOURNAL_PATH
        journal_path.parent.mkdir(parents=True, exist_ok=True)
        with open(journal_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        return entry

    _write_self_composition(root, msg, now)
    _force_fresh_composition(root)
    _refresh_prompt_compositions(root)
    comp_match = _select_composition(root, now, msg, session_n=session_n)
    comp = comp_match['entry'] if comp_match else None

    # Extract signals from composition if available
    signals = {}
    deleted_words = []
    rewrites = []
    cog_state = 'unknown'
    binding = {
        'matched': False,
        'source': None,
        'age_ms': None,
        'key': None,
    }
    if comp_match and comp:
        binding = {
            'matched': True,
            'source': comp_match['source'],
            'age_ms': comp_match['age_ms'],
            'key': comp_match['key'],
            'match_score': round(comp_match['match_score'], 3),
        }
        cs = comp.get('chat_state', comp.get('signals', {}))
        sigs = cs.get('signals', cs) if isinstance(cs, dict) else {}
        signals = {
            'wpm':                sigs.get('wpm', 0),
            'chars_per_sec':      sigs.get('chars_per_sec', 0),
            'deletion_ratio':     sigs.get('deletion_ratio', comp.get('deletion_ratio', 0)),
            'hesitation_count':   sigs.get('hesitation_count', 0),
            'rewrite_count':      sigs.get('rewrite_count', 0),
            'typo_corrections':   comp.get('typo_corrections', sigs.get('typo_corrections', 0)),
            'intentional_deletions': comp.get('intentional_deletions', sigs.get('intentional_deletions', 0)),
            'total_keystrokes':   comp.get('total_keystrokes', 0),
            'duration_ms':        comp.get('duration_ms', 0),
        }
        cog_state = cs.get('state', 'unknown') if isinstance(cs, dict) else 'unknown'
        intent_deleted_words = [
            w.get('word', w) if isinstance(w, dict) else w
            for w in comp.get('intent_deleted_words', [])
        ]
        deleted_words = intent_deleted_words or [
            w.get('word', w) if isinstance(w, dict) else w
            for w in comp.get('deleted_words', [])
        ]
        rewrites = comp.get('rewrites', [])

    # ── STEP 1: Write raw signal (measured truth only) ──
    try:
        import importlib.util
        _sig_matches = sorted(root.glob('src/u_psg_s026*.py'))
        if _sig_matches:
            _sig_spec = importlib.util.spec_from_file_location('_prompt_signal', _sig_matches[-1])
            if _sig_spec and _sig_spec.loader:
                _sig_mod = importlib.util.module_from_spec(_sig_spec)
                _sig_spec.loader.exec_module(_sig_mod)
                _sig_mod.log_raw_signal(
                    root=root, msg=msg, files_open=files_open,
                    session_n=session_n, signals=signals,
                    deleted_words=deleted_words, rewrites=rewrites,
                    composition_binding=binding,
                )
    except Exception:
        pass  # raw signal write is best-effort — journal still works without it

    # ── STEP 2: Build enriched entry (raw + interpretation) ──
    entry = {
        'ts':               now.isoformat(),
        'session_n':        session_n,
        'msg':              msg,
        'msg_len':          len(msg),
        'files_open':       files_open,
        'prompt_kind':      'meta_hook' if meta_prompt_kind else 'operator',
        # ── classification (DERIVED — not in raw signal) ──
        'intent':           'meta' if meta_prompt_kind else _classify_intent(msg),
        'module_refs':      [] if meta_prompt_kind else _extract_module_refs(msg),
        'cognitive_state':  cog_state,
        # ── typing signals (MEASURED — also in raw signal) ──
        'signals':          signals,
        'composition_binding': binding,
        'deleted_words':    deleted_words,
        'rewrites':         rewrites,
        # ── context snapshot (DERIVED — point-in-time system state) ──
        'task_queue':       _active_tasks(root),
        'hot_modules':      _hot_modules(root),
        'prompt_mutations': _mutation_count(root),
        # ── running stats (DERIVED — aggregated from history) ──
        'running':          _running_stats(root),
        # ── provenance tag ──
        'provenance': {
            'measured': ['ts', 'session_n', 'msg', 'msg_len', 'files_open',
                         'signals', 'deleted_words', 'rewrites', 'composition_binding'],
            'derived':  ['intent', 'module_refs', 'cognitive_state',
                         'task_queue', 'hot_modules', 'prompt_mutations', 'running'],
        },
    }
    if meta_prompt_kind:
        entry['meta_prompt_kind'] = meta_prompt_kind

    if _should_skip_duplicate_meta_prompt(root, msg, meta_prompt_kind):
        return entry

    # ── STEP 2b: numeric encoding — prompt_vec + intent_job ──
    # Encodes prompt as sparse word-id vector for context-select agent.
    # intent_job persists until cleared by copilot + tester + operator.
    if not meta_prompt_kind:
        try:
            from src.intent_numeric_seq001_v004_d0420__word_number_file_mapping_for_lc_chore_pigeon_rename_cascade import prompt_to_vector
            pvec = prompt_to_vector(msg)
            if pvec:
                entry['prompt_vec'] = {str(k): round(v, 4) for k, v in pvec.items()}
                # Emit intent job — lives until multi-actor clearance
                _ij_path = root / 'logs' / 'intent_jobs.jsonl'
                _ij_path.parent.mkdir(parents=True, exist_ok=True)
                with open(_ij_path, 'a', encoding='utf-8') as _ijf:
                    _ijf.write(json.dumps({
                        'ts': now.isoformat(),
                        'session_n': session_n,
                        'intent_text': msg[:300],
                        'intent_category': entry.get('intent', 'unknown'),
                        'prompt_vec': entry['prompt_vec'],
                        'status': 'pending',
                        'actors_cleared': [],
                        'module_refs': entry.get('module_refs', []),
                    }, ensure_ascii=False) + '\n')
        except Exception:
            pass  # numeric encoding is best-effort

    # Append
    journal_path = root / JOURNAL_PATH
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    with open(journal_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    if meta_prompt_kind:
        return entry

    entry['_root'] = root  # transient — used by _build_snapshot for coaching bullets
    snapshot = _build_snapshot(entry)
    entry.pop('_root', None)  # don't persist in journal
    _write_latest_snapshot(root, snapshot)
    _refresh_copilot_instructions(root, snapshot)

    # ── Gemini prompt enrichment — inject what operator actually means ──
    # NOTE: classify_bridge also fires this on every submit (primary path).
    # This is the fallback path — fires from the journal command.
    # Wrapped in subprocess with timeout so it can't stall the journal.
    try:
        import subprocess as _sp
        _matches = sorted(root.glob('src/u_pe_s024*.py'))
        if _matches:
            _enricher_path = str(_matches[-1])
            _cog_json = json.dumps({
                'state': cog_state,
                'wpm': signals.get('wpm', 0),
                'del_ratio': signals.get('deletion_ratio', 0),
                'hes': signals.get('hesitation_count', 0),
            })
            _del_json = json.dumps(deleted_words)
            _script = (
                f'import importlib.util, json, sys; '
                f'spec = importlib.util.spec_from_file_location("_e", r"{_enricher_path}"); '
                f'mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); '
                f'mod.inject_query_block(sys.argv[1], sys.argv[2], '
                f'deleted_words=json.loads(sys.argv[3]), '
                f'cognitive_state=json.loads(sys.argv[4]))'
            )
            _proc = _sp.run(
                [sys.executable, '-c', _script, str(root), msg, _del_json, _cog_json],
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
            if _proc.returncode != 0:
                _err = (_proc.stderr or _proc.stdout or '').strip()
                if not _err:
                    _err = f'enricher exited with code {_proc.returncode}'
                raise RuntimeError(_trim_text(_err, 400))
    except Exception as _enrich_err:
        # Log enricher failures so they're not invisible
        try:
            _err_path = root / 'logs' / 'enricher_errors.jsonl'
            _err_path.parent.mkdir(parents=True, exist_ok=True)
            with open(_err_path, 'a', encoding='utf-8') as _ef:
                _ef.write(json.dumps({
                    'ts': datetime.now(timezone.utc).isoformat(),
                    'error': str(_enrich_err),
                    'msg_preview': msg[:80],
                }) + '\n')
        except Exception:
            pass

    # ── Training pair (prompt-side) — response backfilled by rework detector ──
    try:
        import importlib.util as _tw_ilu
        _tw_matches = sorted(root.glob('src/训w_trwr_s028*.py'))
        if _tw_matches:
            _tw_spec = _tw_ilu.spec_from_file_location('_tw', _tw_matches[-1])
            if _tw_spec is not None and _tw_spec.loader is not None:
                _tw_mod = _tw_ilu.module_from_spec(_tw_spec)
                _tw_spec.loader.exec_module(_tw_mod)
                _tw_mod.write_training_pair(
                    root,
                    prompt=msg[:500],
                    response='(pending — response not yet captured)',
                    verdict='pending',
                )
    except Exception:
        pass

    # ── Staleness alert — detect stale managed blocks ──
    try:
        import importlib.util as _sa_ilu
        _sa_matches = sorted(root.glob('src/警p_sa_s030*.py'))
        if _sa_matches:
            _sa_spec = _sa_ilu.spec_from_file_location('_staleness', _sa_matches[-1])
            if _sa_spec is not None and _sa_spec.loader is not None:
                _sa_mod = _sa_ilu.module_from_spec(_sa_spec)
                _sa_spec.loader.exec_module(_sa_mod)
                _sa_mod.inject_staleness_alert(root)
    except Exception:
        pass

    return entry
