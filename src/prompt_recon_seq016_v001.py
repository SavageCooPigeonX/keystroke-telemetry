"""Automated prompt reconstruction — processes os_keystrokes into structured JSON."""

# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# ── /pulse ──

import json
import hashlib
import sys
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from client.chat_composition_analyzer import (
    reconstruct_composition, classify_chat_state, _read_messages,
)

COMPOSITIONS_LOG = Path('logs/prompt_compositions.jsonl')


def _hash_events(events: list) -> str:
    raw = ''.join(f'{e.get("ts",0)}{e.get("key","")}' for e in events[:20])
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def _load_existing_hashes(log_path: Path) -> set:
    if not log_path.exists():
        return set()
    hashes = set()
    for line in log_path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        try:
            hashes.add(json.loads(line).get('event_hash', ''))
        except (json.JSONDecodeError, KeyError):
            pass
    return hashes


def reconstruct_all(root: Path) -> list[dict]:
    """Process every prompt session in os_keystrokes.jsonl.

    Deduplicates against existing entries in prompt_compositions.jsonl.
    Returns list of NEW entries written.
    """
    log_path = root / 'logs' / 'os_keystrokes.jsonl'
    out_path = root / COMPOSITIONS_LOG
    out_path.parent.mkdir(parents=True, exist_ok=True)

    messages = _read_messages(log_path)
    if not messages:
        return []

    existing = _load_existing_hashes(out_path)
    new_entries = []

    for idx, msg_events in enumerate(messages):
        eh = _hash_events(msg_events)
        if eh in existing:
            continue

        comp = reconstruct_composition(msg_events)
        state = classify_chat_state(comp)

        # Skip empty submits (just Enter with no content)
        if comp['total_keystrokes'] < 3:
            continue

        deleted_words = [w['word'] for w in comp['deleted_words']]
        rewrites = [{'old': r['old'], 'new': r['new']} for r in comp['rewrites']]

        entry = {
            'event_hash': eh,
            'session_idx': idx,
            'ts': datetime.now(timezone.utc).isoformat(),
            'first_key_ts': msg_events[0].get('ts', 0),
            'last_key_ts': msg_events[-1].get('ts', 0),
            'final_text': comp['final_text'],
            'peak_buffer': comp['peak_buffer'],
            'deleted_words': deleted_words,
            'rewrites': rewrites,
            'hesitation_windows': comp['hesitation_windows'],
            'cognitive_state': state['state'],
            'state_confidence': state['confidence'],
            'signals': state['signals'],
            'deletion_ratio': comp['deletion_ratio'],
            'total_keystrokes': comp['total_keystrokes'],
            'duration_ms': comp['duration_ms'],
            'chars_per_sec': comp['chars_per_sec'],
            'typo_corrections': comp['typo_corrections'],
            'intentional_deletions': comp['intentional_deletions'],
        }

        new_entries.append(entry)
        existing.add(eh)

    # Append all new entries
    if new_entries:
        with open(out_path, 'a', encoding='utf-8') as f:
            for entry in new_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    return new_entries


def build_mutation_audit(root: Path) -> dict:
    """Analyze how prompts mutated across the session.

    Returns a structured audit: deletion trends, recurring deleted words,
    cognitive state progression, rewrite patterns.
    """
    log_path = root / COMPOSITIONS_LOG
    if not log_path.exists():
        return {'error': 'no prompt_compositions.jsonl — run reconstruct_all first'}

    entries = []
    for line in log_path.read_text(encoding='utf-8').splitlines():
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    if not entries:
        return {'prompts': 0}

    entries.sort(key=lambda e: e.get('first_key_ts', 0))

    # Aggregate
    all_deleted = []
    all_rewrites = []
    states = []
    del_ratios = []
    durations = []

    for e in entries:
        all_deleted.extend(e.get('deleted_words', []))
        all_rewrites.extend(e.get('rewrites', []))
        states.append(e.get('cognitive_state', 'neutral'))
        del_ratios.append(e.get('deletion_ratio', 0))
        durations.append(e.get('duration_ms', 0))

    # Word frequency in deletions
    word_freq = {}
    for w in all_deleted:
        wl = w.lower().strip()
        if len(wl) >= 2:
            word_freq[wl] = word_freq.get(wl, 0) + 1
    top_deleted = sorted(word_freq.items(), key=lambda x: -x[1])[:15]

    # State progression
    state_counts = {}
    for s in states:
        state_counts[s] = state_counts.get(s, 0) + 1

    # Trend: split into thirds
    n = len(del_ratios)
    third = max(1, n // 3)
    early = del_ratios[:third]
    mid = del_ratios[third:2*third]
    late = del_ratios[2*third:]
    trend = {
        'early_avg_deletion': round(sum(early)/max(len(early),1), 3),
        'mid_avg_deletion': round(sum(mid)/max(len(mid),1), 3),
        'late_avg_deletion': round(sum(late)/max(len(late),1), 3),
    }

    return {
        'prompts': len(entries),
        'total_deleted_words': len(all_deleted),
        'total_rewrites': len(all_rewrites),
        'unique_deleted_words': len(word_freq),
        'top_deleted_words': top_deleted,
        'state_distribution': state_counts,
        'deletion_trend': trend,
        'avg_deletion_ratio': round(sum(del_ratios)/max(len(del_ratios),1), 3),
        'avg_duration_ms': round(sum(durations)/max(len(durations),1)),
        'all_deleted_words': all_deleted,
        'all_rewrites': all_rewrites,
    }


def get_latest_composition(root: Path, n: int = 1) -> list[dict]:
    """Get the last N composition entries from prompt_compositions.jsonl."""
    log_path = root / COMPOSITIONS_LOG
    if not log_path.exists():
        return []
    lines = log_path.read_text(encoding='utf-8').strip().splitlines()
    results = []
    for line in lines[-n:]:
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return results


if __name__ == '__main__':
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path('.')

    # Reconstruct all prompts
    new = reconstruct_all(root)
    print(f'Reconstructed {len(new)} new prompt(s)')

    # Build mutation audit
    audit = build_mutation_audit(root)
    print(json.dumps(audit, ensure_ascii=False, indent=2))

    # Write audit snapshot
    audit_path = root / 'logs' / 'prompt_mutation_audit.json'
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Audit written to {audit_path}')
