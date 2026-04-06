# ┌────────────────────────────────────────────────────────────┐
# │  training_pairs_seq027_v001                               │
# │  Intent alignment training data — every edit is a label.  │
# │  User intent (keystrokes) vs Copilot intent (edit_why).   │
# │  Fires per-edit and per-push-cycle.                       │
# └────────────────────────────────────────────────────────────┘


"""
Training pair generator for the intent alignment loop.

Per-edit:  capture_training_pair(root) → reads latest edit_pair + journal + rework
           Writes to logs/training_pairs.jsonl

Per-cycle: generate_cycle_summary(root, cycle_dict) → reads all pairs since last push
           Writes to logs/training_cycle_summaries.jsonl

The delta between user_intent and copilot_intent IS the gradient.
"""


from __future__ import annotations
import json
import re
from pathlib import Path
from datetime import datetime, timezone


def _load_jsonl_tail(filepath: Path, max_lines: int = 50) -> list[dict]:
    """Read last N lines of a JSONL file."""
    if not filepath.exists():
        return []
    try:
        data = filepath.read_bytes()
        lines = data.decode('utf-8', errors='replace').strip().split('\n')
        results = []
        for line in lines[-max_lines:]:
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return results
    except OSError:
        return []


def _normalize_text(text: str) -> str:
    return ' '.join(str(text or '').lower().split())


def _summarize_text(text: str, max_chars: int = 220) -> str:
    cleaned = re.sub(r'\s+', ' ', str(text or '')).strip()
    if not cleaned:
        return ''
    if len(cleaned) <= max_chars:
        return cleaned
    for sep in ('. ', '! ', '? '):
        idx = cleaned.find(sep)
        if 0 < idx < max_chars:
            return cleaned[:idx + 1].strip()
    return cleaned[:max_chars - 3].rstrip() + '...'


def _find_response_for_prompt(prompt_msg: str, response_entries: list[dict]) -> dict | None:
    prompt_norm = _normalize_text(prompt_msg)
    if not prompt_norm:
        return None
    prompt_head = prompt_norm[:80]
    for entry in reversed(response_entries):
        response_prompt = _normalize_text(entry.get('prompt', ''))
        if not response_prompt:
            continue
        if response_prompt == prompt_norm:
            return entry
        if prompt_head and response_prompt[:80] == prompt_head:
            return entry
        if len(prompt_head) >= 24 and (prompt_head in response_prompt or response_prompt[:48] in prompt_norm):
            return entry
    return None


def _build_work_note(edit_pair: dict, copilot_intent: dict) -> str:
    parts = []
    edit_why = str(edit_pair.get('edit_why', '')).strip()
    if edit_why:
        parts.append(edit_why)
    file_name = Path(str(copilot_intent.get('file', '') or edit_pair.get('file', ''))).name
    if file_name:
        parts.append(f'@{file_name}')
    deltas = []
    lines_added = int(copilot_intent.get('lines_added', 0) or 0)
    chars_inserted = int(copilot_intent.get('chars_inserted', 0) or 0)
    if lines_added:
        deltas.append(f'+{lines_added}L')
    if chars_inserted:
        deltas.append(f'+{chars_inserted}c')
    if deltas:
        parts.append(f'({", ".join(deltas)})')
    return ' '.join(parts).strip()[:220]


def _build_completion_note(work_note: str, response_summary: str) -> str:
    if work_note and response_summary:
        return _summarize_text(f'{work_note}. {response_summary}', max_chars=240)
    return work_note or response_summary


def _top_counts(items: list[str], limit: int = 5) -> list[dict]:
    counts: dict[str, int] = {}
    for item in items:
        key = str(item or '').strip()
        if not key:
            continue
        counts[key] = counts.get(key, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [{'value': value, 'count': count} for value, count in ranked[:limit]]


def _classify_user_intent(journal_entry: dict) -> dict:
    """Extract structured user intent from prompt journal entry."""
    signals = journal_entry.get('signals', {})
    return {
        'raw_prompt': journal_entry.get('msg', '')[:300],
        'classified_intent': journal_entry.get('intent', 'unknown'),
        'cognitive_state': journal_entry.get('cognitive_state', 'unknown'),
        'wpm': signals.get('wpm', 0),
        'deletion_ratio': signals.get('deletion_ratio', 0),
        'hesitation_count': signals.get('hesitation_count', 0),
        'rewrite_count': signals.get('rewrite_count', 0),
        'deleted_words': journal_entry.get('deleted_words', []),
        'composition_time_ms': signals.get('duration_ms', 0),
    }


def _classify_copilot_intent(edit_pair: dict, copilot_edits: list[dict]) -> dict:
    """Extract structured Copilot intent from edit pair + copilot edit logs."""
    # Find copilot_edits matching this file near the edit timestamp
    file_key = edit_pair.get('file', '')
    edit_ts = edit_pair.get('edit_ts', '')
    matching_edits = [
        e for e in copilot_edits
        if e.get('file', '') == file_key
    ]
    total_chars = sum(e.get('chars_inserted', 0) for e in matching_edits)
    total_replaced = sum(e.get('chars_replaced', 0) for e in matching_edits)
    total_lines = sum(e.get('lines_added', 0) for e in matching_edits)
    edit_sources = list({e.get('edit_source', 'unknown') for e in matching_edits})
    had_physical = any(e.get('had_physical_keystroke', False) for e in matching_edits)

    return {
        'edit_why': edit_pair.get('edit_why', ''),
        'file': file_key,
        'edit_ts': edit_ts,
        'chars_inserted': total_chars,
        'chars_replaced': total_replaced,
        'lines_added': total_lines,
        'edit_sources': edit_sources,
        'had_physical_keystroke': had_physical,
        'latency_ms': edit_pair.get('latency_ms', 0),
    }


def _find_rework_for_prompt(prompt_msg: str, rework_entries: list[dict]) -> dict | None:
    """Find rework score matching this prompt (by hint prefix)."""
    if not prompt_msg:
        return None
    prefix = prompt_msg[:80].lower()
    for entry in reversed(rework_entries):
        hint = (entry.get('query_hint', '') or '').lower()
        if hint and prefix[:40] in hint:
            return entry
    return None


def capture_training_pair(root: Path) -> dict | None:
    """
    Capture a training pair from the latest edit cycle.

    Reads: latest edit_pair, matching journal entry, copilot_edits, rework.
    Writes: one record to logs/training_pairs.jsonl
    Returns: the training record or None.
    """
    root = Path(root)
    logs = root / 'logs'

    # Load latest edit pair
    edit_pairs = _load_jsonl_tail(logs / 'edit_pairs.jsonl', max_lines=5)
    if not edit_pairs:
        return None
    latest_edit = edit_pairs[-1]

    # Load matching journal entry (by session_n or timestamp proximity)
    journal_entries = _load_jsonl_tail(logs / 'prompt_journal.jsonl', max_lines=20)
    session_n = latest_edit.get('session_n', 0)
    journal_match = None
    for entry in reversed(journal_entries):
        if entry.get('session_n') == session_n:
            journal_match = entry
            break
    if not journal_match and journal_entries:
        journal_match = journal_entries[-1]

    # Load recent copilot edits
    copilot_edits = _load_jsonl_tail(logs / 'copilot_edits.jsonl', max_lines=50)

    # Load recent captured AI responses for this prompt
    ai_responses = _load_jsonl_tail(logs / 'ai_responses.jsonl', max_lines=100)

    # Load rework log
    rework_entries = []
    rework_path = root / 'rework_log.json'
    if rework_path.exists():
        try:
            rework_entries = json.loads(rework_path.read_text(encoding='utf-8'))
            if not isinstance(rework_entries, list):
                rework_entries = []
        except (json.JSONDecodeError, OSError):
            pass

    # Build the training record
    user_intent = _classify_user_intent(journal_match) if journal_match else {}
    copilot_intent = _classify_copilot_intent(latest_edit, copilot_edits)
    rework = _find_rework_for_prompt(
        user_intent.get('raw_prompt', ''), rework_entries
    )
    response_match = _find_response_for_prompt(
        user_intent.get('raw_prompt', '') or latest_edit.get('prompt_msg', ''),
        ai_responses,
    )
    response_summary = _summarize_text((response_match or {}).get('response', ''))
    work_note = _build_work_note(latest_edit, copilot_intent)
    completion_note = _build_completion_note(work_note, response_summary)

    record = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'cycle': 'per_edit',
        'session_n': session_n,
        'user_intent': user_intent,
        'copilot_intent': copilot_intent,
        'alignment': {
            'rework_score': rework.get('rework_score', None) if rework else None,
            'rework_verdict': rework.get('verdict', None) if rework else None,
            'latency_ms': copilot_intent.get('latency_ms', 0),
            'had_physical_keystroke': copilot_intent.get('had_physical_keystroke', False),
            'user_deletion_ratio': user_intent.get('deletion_ratio', 0),
            'user_hesitation': user_intent.get('hesitation_count', 0),
            'response_captured': bool(response_match),
        },
        'completion': {
            'work_note': work_note,
            'completion_note': completion_note,
            'response_summary': response_summary,
            'response_ts': (response_match or {}).get('ts', ''),
            'response_id': (response_match or {}).get('response_id', ''),
        },
    }

    # Write
    out_path = logs / 'training_pairs.jsonl'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record) + '\n')

    return record


def generate_cycle_summary(root: Path, cycle: dict | None = None) -> dict:
    """
    Generate a training summary for the push cycle.

    Reads all training_pairs since last push, scores intent alignment,
    and writes a summary to logs/training_cycle_summaries.jsonl.

    If `cycle` is provided (from run_push_cycle), it's merged into the summary.
    """
    root = Path(root)
    logs = root / 'logs'

    # Load all training pairs
    all_pairs = _load_jsonl_tail(logs / 'training_pairs.jsonl', max_lines=200)

    # Load push state to find cycle boundary
    state_path = logs / 'push_cycle_state.json'
    last_push_ts = ''
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding='utf-8'))
            last_push_ts = state.get('last_push_ts', '')
        except (json.JSONDecodeError, OSError):
            pass

    # Filter pairs from this cycle
    cycle_pairs = all_pairs  # default: all
    if last_push_ts:
        cycle_pairs = [p for p in all_pairs if p.get('ts', '') > last_push_ts]

    if not cycle_pairs:
        return {'status': 'no_pairs', 'count': 0}

    # Compute alignment metrics
    rework_scores = [
        p['alignment']['rework_score']
        for p in cycle_pairs
        if p.get('alignment', {}).get('rework_score') is not None
    ]
    latencies = [
        p['alignment']['latency_ms']
        for p in cycle_pairs
        if p.get('alignment', {}).get('latency_ms')
    ]
    deletion_ratios = [
        p['user_intent']['deletion_ratio']
        for p in cycle_pairs
        if p.get('user_intent', {}).get('deletion_ratio') is not None
    ]
    physical_keystroke_rate = (
        sum(1 for p in cycle_pairs if p.get('alignment', {}).get('had_physical_keystroke'))
        / len(cycle_pairs) if cycle_pairs else 0
    )
    response_capture_rate = (
        sum(1 for p in cycle_pairs if p.get('alignment', {}).get('response_captured'))
        / len(cycle_pairs) if cycle_pairs else 0
    )

    # Intent classification distribution
    intents = {}
    for p in cycle_pairs:
        intent = p.get('user_intent', {}).get('classified_intent', 'unknown')
        intents[intent] = intents.get(intent, 0) + 1

    # Edit source distribution
    sources = {}
    for p in cycle_pairs:
        for src in p.get('copilot_intent', {}).get('edit_sources', ['unknown']):
            sources[src] = sources.get(src, 0) + 1

    # Files touched
    files = list({p.get('copilot_intent', {}).get('file', '') for p in cycle_pairs})
    completion_notes = [
        p.get('completion', {}).get('completion_note', '')
        for p in cycle_pairs
        if p.get('completion', {}).get('completion_note')
    ]
    work_notes = [
        p.get('completion', {}).get('work_note', '')
        for p in cycle_pairs
        if p.get('completion', {}).get('work_note')
    ]
    response_summaries = [
        p.get('completion', {}).get('response_summary', '')
        for p in cycle_pairs
        if p.get('completion', {}).get('response_summary')
    ]

    summary = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'cycle': 'push_summary',
        'pair_count': len(cycle_pairs),
        'metrics': {
            'avg_rework_score': round(sum(rework_scores) / len(rework_scores), 3) if rework_scores else None,
            'avg_latency_ms': round(sum(latencies) / len(latencies)) if latencies else None,
            'avg_deletion_ratio': round(sum(deletion_ratios) / len(deletion_ratios), 3) if deletion_ratios else None,
            'physical_keystroke_rate': round(physical_keystroke_rate, 3),
            'response_capture_rate': round(response_capture_rate, 3),
            'rework_scored_count': len(rework_scores),
        },
        'intent_distribution': intents,
        'edit_source_distribution': sources,
        'files_touched': files[:20],
        'completion_summary': {
            'recent_completion_notes': completion_notes[-5:],
            'response_samples': response_summaries[-3:],
            'top_work_notes': _top_counts(work_notes),
        },
    }

    # Merge push cycle data if available
    if cycle:
        summary['push_cycle'] = {
            'cycle_number': cycle.get('cycle_number'),
            'sync_score': cycle.get('sync', {}).get('score'),
            'prediction_f1': cycle.get('prediction_score', {}).get('avg_f1'),
            'predictions_fired': cycle.get('new_predictions', 0),
            'backward_runs': cycle.get('backward_runs', 0),
            'prompt_count': cycle.get('operator_signal', {}).get('prompt_count', 0),
            'response_count': len(response_summaries),
        }

    # Write
    out_path = logs / 'training_cycle_summaries.jsonl'
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(summary) + '\n')

    return summary
