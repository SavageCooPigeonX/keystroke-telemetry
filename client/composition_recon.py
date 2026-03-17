"""
composition_recon.py — Composition Buffer Reconstruction

Tier 3 of the telemetry waterfall. Reconstructs what operators typed,
deleted, and rewrote before submitting a prompt.

Three data sources fused:
  1. OS hook keystrokes (logs/os_keystrokes.jsonl) — raw key-by-key timing
  2. vscdb drafts (logs/vscdb_drafts.jsonl) — draft composition snapshots
  3. chat prompts (logs/chat_prompts.jsonl) — final submitted text
  + prompt journal (logs/prompt_journal.jsonl) — LLM-received text

Outputs to logs/composition_recon.jsonl:
  - deletion_ratio: keystrokes_total / final_text_length
  - abandoned_drafts: drafts that were fully deleted
  - hesitation_windows: gaps > 2s between keystrokes in chat context
  - rewrite_sequences: text that was typed, deleted, retyped differently

Usage: py client/composition_recon.py <project_root> [--once]
"""
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from collections import defaultdict


HESITATION_THRESHOLD_MS = 2000
WINDOW_MINUTES = 5


def load_jsonl(path: str, max_age_minutes: int = 0) -> list[dict]:
    """Load JSONL file, optionally filtering by age."""
    if not os.path.exists(path):
        return []
    entries = []
    cutoff = None
    if max_age_minutes > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=max_age_minutes)
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if cutoff and 'ts' in entry:
                    try:
                        raw_ts = entry['ts']
                        if isinstance(raw_ts, (int, float)):
                            ts = datetime.fromtimestamp(raw_ts, tz=timezone.utc)
                        else:
                            ts = datetime.fromisoformat(str(raw_ts).replace('Z', '+00:00'))
                        if ts < cutoff:
                            continue
                    except (ValueError, TypeError, OSError):
                        pass
                entries.append(entry)
            except json.JSONDecodeError:
                continue
    return entries


def reconstruct_composition(project_root: str) -> list[dict]:
    """Reconstruct composition buffer activity from all three tiers."""
    logs = os.path.join(project_root, 'logs')

    # Load data sources
    os_keys = load_jsonl(os.path.join(logs, 'os_keystrokes.jsonl'), WINDOW_MINUTES)
    vscdb = load_jsonl(os.path.join(logs, 'vscdb_drafts.jsonl'), WINDOW_MINUTES)
    chat_prompts = load_jsonl(os.path.join(logs, 'chat_prompts.jsonl'), WINDOW_MINUTES)
    journal = load_jsonl(os.path.join(logs, 'prompt_journal.jsonl'), WINDOW_MINUTES)

    results = []

    # ── Analyze OS hook chat keystrokes ──
    chat_sessions: list[dict] = []
    current_session: dict | None = None

    for entry in os_keys:
        ctx = entry.get('context', '')
        if ctx != 'chat':
            if current_session and current_session['keys']:
                chat_sessions.append(current_session)
                current_session = None
            continue

        if current_session is None:
            current_session = {
                'start_ts': entry.get('ts', ''),
                'keys': [],
                'buffer_snapshots': [],
            }

        keys = entry.get('keys', [])
        for k in keys:
            current_session['keys'].append(k)

        buf = entry.get('buffer', '')
        if buf:
            current_session['buffer_snapshots'].append({
                'ts': entry.get('ts', ''),
                'text': buf,
            })

    if current_session and current_session['keys']:
        chat_sessions.append(current_session)

    # ── For each chat session, compute metrics ──
    for session in chat_sessions:
        keys = session['keys']
        total_keystrokes = len(keys)
        backspaces = sum(1 for k in keys if isinstance(k, dict) and k.get('key') == 'Key.backspace')
        inserts = total_keystrokes - backspaces

        # Find hesitation windows (gaps > threshold between consecutive keys)
        hesitations = []
        timestamps = []
        for k in keys:
            if isinstance(k, dict) and 'ts' in k:
                try:
                    t = float(k['ts'])
                    timestamps.append(t)
                except (ValueError, TypeError):
                    pass

        for i in range(1, len(timestamps)):
            gap_ms = (timestamps[i] - timestamps[i - 1]) * 1000
            if gap_ms > HESITATION_THRESHOLD_MS:
                hesitations.append({
                    'at_keystroke': i,
                    'gap_ms': round(gap_ms),
                })

        # Get final buffer state
        final_buffer = ''
        if session['buffer_snapshots']:
            final_buffer = session['buffer_snapshots'][-1]['text']

        # Deletion ratio: how much was typed vs how much survived
        deletion_ratio = backspaces / max(inserts, 1)

        results.append({
            'type': 'os_hook_session',
            'start_ts': session['start_ts'],
            'total_keystrokes': total_keystrokes,
            'inserts': inserts,
            'backspaces': backspaces,
            'deletion_ratio': round(deletion_ratio, 3),
            'hesitation_windows': hesitations[:20],
            'final_buffer': final_buffer[:500],
            'buffer_snapshots': len(session['buffer_snapshots']),
        })

    # ── Analyze vscdb draft changes ──
    draft_changes = [e for e in vscdb if e.get('event') == 'draft_changed']
    abandoned_drafts = []
    rewrite_sequences = []

    for i, change in enumerate(draft_changes):
        prev = change.get('prev_text', '')
        new = change.get('new_text', '')

        # Abandoned draft: had text, now empty
        if prev and not new:
            abandoned_drafts.append({
                'ts': change.get('ts', ''),
                'abandoned_text': prev[:500],
                'char_count': len(prev),
            })

        # Rewrite: significant change in text
        elif prev and new and prev != new:
            # Compute edit distance approximation
            common_prefix = 0
            for a, b in zip(prev, new):
                if a == b:
                    common_prefix += 1
                else:
                    break
            change_ratio = 1 - (common_prefix / max(len(prev), len(new)))
            if change_ratio > 0.3:  # >30% changed = rewrite
                rewrite_sequences.append({
                    'ts': change.get('ts', ''),
                    'from_text': prev[:300],
                    'to_text': new[:300],
                    'change_ratio': round(change_ratio, 3),
                })

    if abandoned_drafts:
        results.append({
            'type': 'abandoned_drafts',
            'count': len(abandoned_drafts),
            'drafts': abandoned_drafts[:10],
        })

    if rewrite_sequences:
        results.append({
            'type': 'rewrite_sequences',
            'count': len(rewrite_sequences),
            'rewrites': rewrite_sequences[:10],
        })

    # ── Match submitted prompts with OS hook data ──
    submitted = [e for e in vscdb if e.get('event') == 'prompt_submitted']
    for prompt in submitted[-5:]:  # last 5
        text = prompt.get('text', '')
        if not text:
            continue

        # Find closest chat session by time
        best_session = None
        best_gap = float('inf')
        prompt_ts = prompt.get('ts', '')

        for r in results:
            if r.get('type') != 'os_hook_session':
                continue
            session_ts = r.get('start_ts', '')
            if session_ts and prompt_ts:
                try:
                    pt = datetime.fromisoformat(prompt_ts.replace('Z', '+00:00'))
                    st = datetime.fromisoformat(session_ts.replace('Z', '+00:00'))
                    gap = abs((pt - st).total_seconds())
                    if gap < best_gap:
                        best_gap = gap
                        best_session = r
                except (ValueError, TypeError):
                    pass

        composition_analysis = {
            'type': 'prompt_composition',
            'ts': prompt_ts,
            'final_text': text[:500],
            'final_length': len(text),
            'model': prompt.get('model', ''),
        }

        if best_session and best_gap < 300:  # within 5 minutes
            composition_analysis['total_keystrokes'] = best_session['total_keystrokes']
            composition_analysis['deletion_ratio'] = best_session['deletion_ratio']
            composition_analysis['effort_ratio'] = round(
                best_session['total_keystrokes'] / max(len(text), 1), 2
            )
            composition_analysis['hesitation_count'] = len(best_session['hesitation_windows'])

        results.append(composition_analysis)

    return results


def main():
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'usage: py composition_recon.py <root> [--once]'}))
        sys.exit(1)

    project_root = sys.argv[1]
    once = '--once' in sys.argv
    log_path = os.path.join(project_root, 'logs', 'composition_recon.jsonl')

    if once:
        results = reconstruct_composition(project_root)
        ts = datetime.now(timezone.utc).isoformat()
        entry = json.dumps({
            'ts': ts,
            'results': results,
            'source_counts': {
                'os_hook_sessions': sum(1 for r in results if r.get('type') == 'os_hook_session'),
                'abandoned_drafts': sum(1 for r in results if r.get('type') == 'abandoned_drafts'),
                'rewrite_sequences': sum(1 for r in results if r.get('type') == 'rewrite_sequences'),
                'prompt_compositions': sum(1 for r in results if r.get('type') == 'prompt_composition'),
            },
        }, ensure_ascii=False) + '\n'
        try:
            with open(log_path, 'a', encoding='utf-8') as f:
                f.write(entry)
        except OSError:
            pass
        print(json.dumps({'status': 'done', 'results': len(results)}))
        return

    # Continuous mode: reconstruct every 30 seconds
    import time
    print(json.dumps({'status': 'started', 'pid': os.getpid()}), flush=True)
    while True:
        time.sleep(30)
        results = reconstruct_composition(project_root)
        if results:
            ts = datetime.now(timezone.utc).isoformat()
            entry = json.dumps({
                'ts': ts,
                'results': results,
            }, ensure_ascii=False) + '\n'
            try:
                with open(log_path, 'a', encoding='utf-8') as f:
                    f.write(entry)
            except OSError:
                pass


if __name__ == '__main__':
    main()
