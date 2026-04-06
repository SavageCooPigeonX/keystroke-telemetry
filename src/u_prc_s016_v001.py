"""Automated prompt reconstruction — processes os_keystrokes into structured JSON."""


import json
import hashlib
import subprocess
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


def _build_entry(msg_events: list, session_idx: int) -> dict | None:
    eh = _hash_events(msg_events)
    comp = reconstruct_composition(msg_events)
    state = classify_chat_state(comp)

    # Skip empty submits (just Enter with no content)
    if comp['total_keystrokes'] < 3:
        return None

    deleted_words = [w['word'] for w in comp['deleted_words']]
    rewrites = [{'old': r['old'], 'new': r['new']} for r in comp['rewrites']]

    return {
        'event_hash': eh,
        'session_idx': session_idx,
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


def _read_latest_message_fallback(log_path: Path) -> list[dict]:
    """Return the latest submit/discard-bounded raw event block from the log."""
    if not log_path.exists():
        return []

    events = []
    for line in log_path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        try:
            evt = json.loads(line)
        except json.JSONDecodeError:
            continue
        if evt.get('source') == 'vscode':
            continue
        if evt.get('type') not in ('insert', 'backspace', 'submit', 'discard'):
            continue
        events.append(evt)

    if not events:
        return []

    block = []
    seen_terminal = False
    for evt in reversed(events):
        block.append(evt)
        if evt.get('type') in ('submit', 'discard'):
            if seen_terminal:
                block.pop()
                break
            seen_terminal = True
            continue
        if seen_terminal:
            continue

    if not seen_terminal:
        return []

    block.reverse()
    return block


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

        entry = _build_entry(msg_events, idx)
        if entry is None:
            continue

        new_entries.append(entry)
        existing.add(eh)

    # Append all new entries
    if new_entries:
        with open(out_path, 'a', encoding='utf-8') as f:
            for entry in new_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    return new_entries


def reconstruct_latest(root: Path) -> dict | None:
    """Reconstruct and append only the latest prompt composition if it is new."""
    log_path = root / 'logs' / 'os_keystrokes.jsonl'
    out_path = root / COMPOSITIONS_LOG
    out_path.parent.mkdir(parents=True, exist_ok=True)

    messages = _read_messages(log_path)
    msg_events = messages[-1] if messages else _read_latest_message_fallback(log_path)
    if not msg_events:
        return None

    event_hash = _hash_events(msg_events)
    existing = _load_existing_hashes(out_path)
    if event_hash in existing:
        latest = get_latest_composition(root, n=1)
        return latest[-1] if latest else None

    session_idx = len(messages) - 1 if messages else 0
    entry = _build_entry(msg_events, session_idx)
    if entry is None:
        return None

    with open(out_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    return entry


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists(): return []
    out = []
    for ln in path.read_text(encoding='utf-8').splitlines():
        if ln.strip():
            try: out.append(json.loads(ln))
            except json.JSONDecodeError: pass
    return out


def build_mutation_audit(root: Path) -> dict:
    """Analyze prompt mutation trends. Writes logs/prompt_mutation_audit.json."""
    entries = _read_jsonl(root / COMPOSITIONS_LOG)
    if not entries: return {'prompts': 0}
    entries.sort(key=lambda e: e.get('first_key_ts', 0))
    all_del, all_rw, states, drs, durs = [], [], [], [], []
    for e in entries:
        all_del.extend(e.get('deleted_words', []))
        all_rw.extend(e.get('rewrites', []))
        states.append(e.get('cognitive_state', 'neutral'))
        drs.append(e.get('deletion_ratio', 0))
        durs.append(e.get('duration_ms', 0))
    wf = {}
    for w in all_del:
        wl = w.lower().strip()
        if len(wl) >= 2: wf[wl] = wf.get(wl, 0) + 1
    sc = {}
    for s in states: sc[s] = sc.get(s, 0) + 1
    t = max(1, len(drs) // 3)
    _avg = lambda xs: round(sum(xs) / max(len(xs), 1), 3)
    return {
        'prompts': len(entries), 'total_deleted_words': len(all_del),
        'total_rewrites': len(all_rw), 'unique_deleted_words': len(wf),
        'top_deleted_words': sorted(wf.items(), key=lambda x: -x[1])[:15],
        'state_distribution': sc,
        'deletion_trend': {'early': _avg(drs[:t]), 'mid': _avg(drs[t:2*t]), 'late': _avg(drs[2*t:])},
        'avg_deletion_ratio': _avg(drs),
        'avg_duration_ms': round(sum(durs) / max(len(durs), 1)),
        'all_deleted_words': all_del, 'all_rewrites': all_rw,
    }


def get_latest_composition(root: Path, n: int = 1) -> list[dict]:
    """Get the last N entries from prompt_compositions.jsonl."""
    return _read_jsonl(root / COMPOSITIONS_LOG)[-n:]


def _snapshot_prompt_state(commit: str, message: str, content: str) -> dict:
    fl = content.split('\n')
    sections = [l.replace('## ', '').strip() for l in fl if l.startswith('## ')]
    features = {
        k: needle in content for k, needle in [
            ('auto_index', 'pigeon:auto-index'),
            ('task_context', 'pigeon:task-context'),
            ('task_queue', 'pigeon:task-queue'),
            ('operator_state', 'pigeon:operator-state'),
            ('prompt_telemetry', 'pigeon:prompt-telemetry'),
            ('prompt_journal', 'prompt_journal'),
            ('pulse_blocks', 'telemetry:pulse'),
            ('prompt_recon', 'prompt_compositions'),
            ('file_consciousness', 'File Consciousness'),
        ]
    }
    op = next((l.strip().replace('**', '') for l in fl if 'Dominant' in l and '|' in l), None)
    return {
        'commit': commit,
        'message': message,
        'content_hash': hashlib.sha256(content.encode()).hexdigest()[:12],
        'lines': content.count('\n'),
        'bytes': len(content),
        'sections': sections,
        'features': features,
        'operator_dominant': op,
    }


def track_copilot_prompt_mutations(root: Path) -> dict:
    """Track .github/copilot-instructions.md mutations. Writes logs/copilot_prompt_mutations.json."""
    ci = '.github/copilot-instructions.md'
    r = subprocess.run(['git', 'log', '--oneline', '--follow', '--', ci],
                       capture_output=True, text=True, encoding='utf-8', cwd=str(root))
    if r.returncode != 0: return {'error': 'git log failed'}
    snaps, prev_h = [], None
    for line in reversed([l.strip() for l in r.stdout.strip().split('\n') if l.strip()]):
        parts = line.split(' ', 1)
        if len(parts) < 2: continue
        h, msg = parts
        cr = subprocess.run(['git', 'show', f'{h}:{ci}'],
                            capture_output=True, text=True, encoding='utf-8', cwd=str(root))
        if cr.returncode != 0: continue
        c = cr.stdout
        ch = hashlib.sha256(c.encode()).hexdigest()[:12]
        if ch == prev_h: continue
        prev_h = ch
        snaps.append(_snapshot_prompt_state(h, msg, c))

    current_path = root / ci
    if current_path.exists():
        current = current_path.read_text(encoding='utf-8')
        current_hash = hashlib.sha256(current.encode()).hexdigest()[:12]
        if not snaps or snaps[-1]['content_hash'] != current_hash:
            snaps.append(_snapshot_prompt_state('WORKTREE', 'current working tree', current))

    result = {'generated': datetime.now(timezone.utc).isoformat(),
              'total_mutations': len(snaps), 'snapshots': snaps,
              'growth': {'initial_lines': snaps[0]['lines'] if snaps else 0,
                         'final_lines': snaps[-1]['lines'] if snaps else 0,
                         'initial_bytes': snaps[0]['bytes'] if snaps else 0,
                         'final_bytes': snaps[-1]['bytes'] if snaps else 0}}
    out = root / 'logs' / 'copilot_prompt_mutations.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    return result


if __name__ == '__main__':
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path('.')

    # Reconstruct all prompts
    new = reconstruct_all(root)
    print(f'Reconstructed {len(new)} new prompt(s)')

    # Build mutation audit
    audit = build_mutation_audit(root)
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    audit_path = root / 'logs' / 'prompt_mutation_audit.json'
    audit_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Audit written to {audit_path}')

    # Track copilot prompt mutations
    mutations = track_copilot_prompt_mutations(root)
    print(f'Copilot prompt: {mutations.get("total_mutations", 0)} mutations tracked')
    if mutations.get('growth'):
        g = mutations['growth']
        print(f'  {g["initial_lines"]} -> {g["final_lines"]} lines ({g["initial_bytes"]} -> {g["final_bytes"]} bytes)')
