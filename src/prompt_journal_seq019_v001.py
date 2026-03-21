"""Enriched prompt journal — every entry cross-references all telemetry.

Replaces the dumb 4-field journal with a full telemetry snapshot per prompt.
Each entry captures: cognitive state, typing signals, deleted words, active
tasks, module heat, session running stats, and intent classification.

Designed for live analysis: grep any field, plot any metric, no aggregation needed.
Zero LLM calls — pure signal cross-referencing.
"""
# ── pigeon ────────────────────────────────────
# SEQ: 019 | VER: v001 | ~190 lines | ~1,800 tokens
# DESC:   enriched_prompt_journal_telemetry
# INTENT: live_telemetry_analysis
# LAST:   2026-03-17
# SESSIONS: 0
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# ── /pulse ──
from __future__ import annotations
import json
import re
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
MAX_COMP_AGE_MS = 60_000     # tight: 60s window
TIGHT_WINDOW_MS = 500        # ±500ms for high-confidence direct binding
MIN_TEXT_MATCH_SCORE = 0.6

PROMPT_BLOCK_START = '<!-- pigeon:prompt-telemetry -->'
PROMPT_BLOCK_END = '<!-- /pigeon:prompt-telemetry -->'

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


def _normalize_prompt_text(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r'\s+', ' ', value)
    return value


def _token_set(value: str) -> set[str]:
    return {token for token in re.findall(r'[a-z0-9]+', value.lower()) if token}


def _text_match_score(msg: str, comp: dict) -> float:
    msg_norm = _normalize_prompt_text(msg)
    if not msg_norm:
        return 0.0

    comp_text = comp.get('final_text') or comp.get('peak_buffer') or ''
    comp_norm = _normalize_prompt_text(comp_text)
    if not comp_norm:
        return 0.0

    if msg_norm == comp_norm:
        return 1.0

    msg_tokens = _token_set(msg_norm)
    comp_tokens = _token_set(comp_norm)
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
        if age > MAX_COMP_AGE_MS:
            continue
        if score < MIN_TEXT_MATCH_SCORE:
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
    if not entries:
        return {}
    n = len(entries)
    # Running averages from entries that have signals
    wpms = [e['signals']['wpm'] for e in entries if 'signals' in e and 'wpm' in e.get('signals', {})]
    dels = [
        e['signals']['deletion_ratio']
        for e in entries
        if isinstance(e.get('signals'), dict) and 'deletion_ratio' in e['signals']
    ]
    states = [e.get('cognitive_state', 'unknown') for e in entries]
    from collections import Counter
    state_dist = dict(Counter(states).most_common(5))

    # Load self-calibration baselines from operator_stats
    baselines = {}
    try:
        import glob, importlib.util
        matches = sorted(root.glob('src/operator_stats_seq008*.py'))
        if matches:
            spec = importlib.util.spec_from_file_location('_os', matches[-1])
            if spec is None or spec.loader is None:
                return {
                    'total_prompts': n,
                    'avg_wpm':       round(sum(wpms) / len(wpms), 1) if wpms else None,
                    'avg_del_ratio': round(sum(dels) / len(dels), 3) if dels else None,
                    'state_distribution': state_dist,
                    'baselines': None,
                }
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            op_path = root / 'operator_profile.md'
            if op_path.exists():
                stats = mod.OperatorStats(str(op_path))
                baselines = mod.compute_baselines(stats._history)
    except Exception:
        pass

    return {
        'total_prompts': n,
        'avg_wpm':       round(sum(wpms) / len(wpms), 1) if wpms else None,
        'avg_del_ratio': round(sum(dels) / len(dels), 3) if dels else None,
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
    return snapshot


def _write_latest_snapshot(root: Path, snapshot: dict) -> None:
    snapshot_path = root / SNAPSHOT_PATH
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def _refresh_copilot_instructions(root: Path, snapshot: dict) -> None:
    try:
        import importlib.util

        manager_path = root / 'src' / 'copilot_prompt_manager_seq020_v001.py'
        if manager_path.exists():
            spec = importlib.util.spec_from_file_location('_copilot_prompt_manager_runtime', manager_path)
            if spec is not None and spec.loader is not None:
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                refresh = getattr(mod, 'refresh_managed_prompt', None)
                if callable(refresh):
                    refresh(root, snapshot=snapshot)
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


def log_enriched_entry(root: Path, msg: str, files_open: list[str],
                       session_n: int) -> dict:
    """Build and append one fully-enriched journal entry. Returns the entry."""
    now = datetime.now(timezone.utc)
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
        deleted_words = [w.get('word', w) if isinstance(w, dict) else w
                         for w in comp.get('deleted_words', [])]
        rewrites = comp.get('rewrites', [])

    entry = {
        'ts':               now.isoformat(),
        'session_n':        session_n,
        'msg':              msg,
        'msg_len':          len(msg),
        'files_open':       files_open,
        # ── classification ──
        'intent':           _classify_intent(msg),
        'module_refs':      _extract_module_refs(msg),
        'cognitive_state':  cog_state,
        # ── typing signals ──
        'signals':          signals,
        'composition_binding': binding,
        'deleted_words':    deleted_words,
        'rewrites':         rewrites,
        # ── context snapshot ──
        'task_queue':       _active_tasks(root),
        'hot_modules':      _hot_modules(root),
        'prompt_mutations': _mutation_count(root),
        # ── running stats ──
        'running':          _running_stats(root),
    }

    # Append
    journal_path = root / JOURNAL_PATH
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    with open(journal_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    entry['_root'] = root  # transient — used by _build_snapshot for coaching bullets
    snapshot = _build_snapshot(entry)
    entry.pop('_root', None)  # don't persist in journal
    _write_latest_snapshot(root, snapshot)
    _refresh_copilot_instructions(root, snapshot)

    return entry
