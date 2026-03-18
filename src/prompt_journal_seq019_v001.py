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
COMPS_PATH     = 'logs/chat_compositions.jsonl'
HEAT_PATH      = 'file_heat_map.json'
TASK_PATH      = 'task_queue.json'
PROFILE_PATH   = 'operator_profile.md'
EDIT_PAIRS     = 'logs/edit_pairs.jsonl'
MUTATIONS_PATH = 'logs/copilot_prompt_mutations.json'

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


def _latest_composition(root: Path) -> dict | None:
    """Read the most recent chat composition entry."""
    p = root / COMPS_PATH
    if not p.exists():
        return None
    try:
        last_line = ''
        with open(p, encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    last_line = line
        return json.loads(last_line) if last_line else None
    except Exception:
        return None


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
    if not data:
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
    dels = [e['signals']['deletion_ratio'] for e in entries if 'signals' in e]
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


def log_enriched_entry(root: Path, msg: str, files_open: list[str],
                       session_n: int) -> dict:
    """Build and append one fully-enriched journal entry. Returns the entry."""
    now = datetime.now(timezone.utc)
    comp = _latest_composition(root)

    # Extract signals from composition if available
    signals = {}
    deleted_words = []
    rewrites = []
    cog_state = 'unknown'
    if comp:
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

    return entry
