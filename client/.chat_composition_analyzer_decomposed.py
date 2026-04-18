"""
chat_composition_analyzer_seq001_v001.py — Reconstructs full chat composition from OS hook.

Bridges raw os_keystrokes.jsonl → structured composition analysis.
Runs after every chat submit, or on-demand from classify_bridge.py.

Extracts:
  - Deleted words/phrases with timestamps
  - Rewrite sequences (typed X, deleted, typed Y at same position)
  - Hesitation windows (pauses > threshold mid-composition)
  - Typo corrections vs intentional deletions
  - Full composition replay for unsaid_analyzer consumption
  - Chat-specific cognitive state signals

Writes to logs/chat_compositions.jsonl

Can be called:
  1. As a module: analyze_latest_composition(root) → dict
  2. From CLI: py client/chat_composition_analyzer_seq001_v001.py <root>
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

# ── Thresholds ───────────────────────────────────────────────────────────────

PAUSE_THRESHOLD_MS = 2000      # 2s pause = hesitation
TYPO_WINDOW_MS = 800           # delete within 800ms of insert = typo
REWRITE_MIN_CHARS = 3          # 3+ chars deleted then retyped = rewrite
INTENT_DELETE_MIN_RUN = 5      # 5+ consecutive backspaces = intent change (not typo)
WORD_BOUNDARY = set(' .,;:!?-\n\t')


# ── Core reconstruction ─────────────────────────────────────────────────────

PAUSE_THRESHOLD_MS = 500

def reconstruct_composition(events: list) -> dict:
    """Reconstruct full composition from keystroke events.

    Args:
        events: list of os_hook events (must have ts, key, type fields)

    Returns:
        {
            'final_text': str,
            'deleted_words': [{'word': str, 'ts': int, 'position': int}],
            'deleted_chars_total': int,
            'rewrites': [{'old': str, 'new': str, 'ts': int, 'position': int}],
            'hesitation_windows': [{'ts': int, 'duration_ms': int, 'buffer_at': str}],
            'typo_corrections': int,
            'intentional_deletions': int,
            'composition_events': [{'ts': int, 'action': str, 'char': str, 'buffer': str}],
            'peak_buffer': str,
            'peak_buffer_len': int,
            'total_keystrokes': int,
            'duration_ms': int,
            'chars_per_sec': float,
            'deletion_ratio': float,
        }
    """
    buffer = ''
    composition_events = []
    deleted_chars = []
    hesitation_windows = []
    peak_buffer = ''
    prev_ts = 0
    delete_run = []
    insert_after_delete = []

    for evt in events:
        buffer, composition_events, deleted_chars, hesitation_windows, peak_buffer, prev_ts, delete_run, insert_after_delete = _reconstruct_composition_process_event(
            evt, buffer, composition_events, deleted_chars, hesitation_windows, peak_buffer, prev_ts, delete_run, insert_after_delete
        )

    deleted_words = _reconstruct_composition_extract_deleted_words(deleted_chars)
    typo_corrections, intentional_deletions = _reconstruct_composition_classify_all_deletions(composition_events)
    intent_deleted_words, intent_delete_chars = _reconstruct_composition_extract_intent_deletions(composition_events)
    rewrites = _reconstruct_composition_extract_rewrites(composition_events)
    stats = _reconstruct_composition_compute_stats(events, buffer, peak_buffer, deleted_chars, composition_events, intent_delete_chars)

    return {
        'final_text': buffer,
        'deleted_words': deleted_words,
        'deleted_chars_total': len(deleted_chars),
        'rewrites': rewrites,
        'hesitation_windows': hesitation_windows,
        'typo_corrections': typo_corrections,
        'intentional_deletions': intentional_deletions,
        'composition_events': composition_events,
        'peak_buffer': peak_buffer,
        'peak_buffer_len': len(peak_buffer),
        'total_keystrokes': stats['total_keys'],
        'duration_ms': stats['duration_ms'],
        'chars_per_sec': stats['chars_per_sec'],
        'deletion_ratio': stats['deletion_ratio'],
        'intent_deleted_words': intent_deleted_words,
        'intent_delete_chars': intent_delete_chars,
        'intent_deletion_ratio': stats['intent_deletion_ratio'],
    }

def _reconstruct_composition_process_event(evt, buffer, composition_events, deleted_chars, hesitation_windows, peak_buffer, prev_ts, delete_run, insert_after_delete):
    ts = evt.get('ts', 0)
    etype = evt.get('type', '')
    key = evt.get('key', '')

    if prev_ts and ts - prev_ts >= PAUSE_THRESHOLD_MS:
        hesitation_windows.append({
            'ts': prev_ts,
            'duration_ms': ts - prev_ts,
            'buffer_at': buffer,
        })

    if etype == 'insert':
        buffer, composition_events, peak_buffer, delete_run, insert_after_delete = _reconstruct_composition_handle_insert(
            ts, key, buffer, composition_events, peak_buffer, delete_run, insert_after_delete
        )
        prev_ts = ts
    elif etype == 'backspace':
        buffer, composition_events, deleted_chars, delete_run = _reconstruct_composition_handle_backspace(
            ts, buffer, composition_events, deleted_chars, delete_run
        )
        prev_ts = ts
    elif etype == 'submit':
        composition_events.append({
            'ts': ts, 'action': 'submit', 'char': '', 'buffer': buffer,
        })
        prev_ts = ts
    elif etype == 'discard':
        composition_events.append({
            'ts': ts, 'action': 'discard', 'char': '', 'buffer': buffer,
        })
        prev_ts = ts
    elif etype == 'selection_replace':
        buffer, composition_events, deleted_chars, peak_buffer = _reconstruct_composition_handle_selection_replace(
            ts, key, evt, buffer, composition_events, deleted_chars, peak_buffer
        )
        prev_ts = ts
    elif etype == 'selection_delete':
        buffer, composition_events, deleted_chars = _reconstruct_composition_handle_selection_delete(
            ts, evt, buffer, composition_events, deleted_chars
        )
        prev_ts = ts
    elif etype == 'paste_replace':
        buffer, composition_events, deleted_chars, peak_buffer = _reconstruct_composition_handle_paste_replace(
            ts, evt, buffer, composition_events, deleted_chars, peak_buffer
        )
        prev_ts = ts
    elif etype == 'paste':
        buffer, composition_events, peak_buffer = _reconstruct_composition_handle_paste(
            ts, evt, buffer, composition_events, peak_buffer
        )
        prev_ts = ts
    elif etype == 'cut':
        buffer, composition_events, deleted_chars = _reconstruct_composition_handle_cut(
            ts, evt, buffer, composition_events, deleted_chars
        )
        prev_ts = ts

    delete_run, insert_after_delete = _reconstruct_composition_flush_delete_run(etype, delete_run, insert_after_delete)

    return buffer, composition_events, deleted_chars, hesitation_windows, peak_buffer, prev_ts, delete_run, insert_after_delete

def _reconstruct_composition_handle_insert(ts, key, buffer, composition_events, peak_buffer, delete_run, insert_after_delete):
    char = key
    buffer += char
    if len(buffer) > len(peak_buffer):
        peak_buffer = buffer
    composition_events.append({
        'ts': ts, 'action': 'insert', 'char': char, 'buffer': buffer,
    })
    if delete_run:
        insert_after_delete.append(char)
    return buffer, composition_events, peak_buffer, delete_run, insert_after_delete

def _reconstruct_composition_handle_backspace(ts, buffer, composition_events, deleted_chars, delete_run):
    if buffer:
        deleted_char = buffer[-1]
        buffer = buffer[:-1]
        deleted_chars.append({'char': deleted_char, 'ts': ts, 'pos': len(buffer)})
        composition_events.append({
            'ts': ts, 'action': 'delete', 'char': deleted_char, 'buffer': buffer,
        })
        delete_run.append({'char': deleted_char, 'ts': ts})
    return buffer, composition_events, deleted_chars, delete_run

def _reconstruct_composition_handle_selection_replace(ts, key, evt, buffer, composition_events, deleted_chars, peak_buffer):
    deleted_text = evt.get('deleted_text', buffer)
    for i, ch in enumerate(reversed(deleted_text)):
        deleted_chars.append({'char': ch, 'ts': ts, 'pos': max(0, len(buffer) - i - 1)})
    composition_events.append({
        'ts': ts, 'action': 'selection_replace',
        'char': key, 'buffer': key,
        'deleted': deleted_text,
    })
    buffer = key
    if len(buffer) > len(peak_buffer):
        peak_buffer = buffer
    return buffer, composition_events, deleted_chars, peak_buffer

def _reconstruct_composition_handle_selection_delete(ts, evt, buffer, composition_events, deleted_chars):
    deleted_text = evt.get('deleted_text', buffer)
    for i, ch in enumerate(reversed(deleted_text)):
        deleted_chars.append({'char': ch, 'ts': ts, 'pos': max(0, len(buffer) - i - 1)})
    composition_events.append({
        'ts': ts, 'action': 'selection_delete',
        'char': '', 'buffer': '',
        'deleted': deleted_text,
    })
    buffer = ''
    return buffer, composition_events, deleted_chars

def _reconstruct_composition_handle_paste_replace(ts, evt, buffer, composition_events, deleted_chars, peak_buffer):
    deleted_text = evt.get('deleted_text', '')
    pasted_text = evt.get('pasted_text', '')
    if deleted_text:
        for i, ch in enumerate(reversed(deleted_text)):
            deleted_chars.append({'char': ch, 'ts': ts, 'pos': max(0, len(buffer) - i - 1)})
    composition_events.append({
        'ts': ts, 'action': 'paste_replace',
        'char': pasted_text, 'buffer': pasted_text,
        'deleted': deleted_text,
    })
    buffer = pasted_text
    if len(buffer) > len(peak_buffer):
        peak_buffer = buffer
    return buffer, composition_events, deleted_chars, peak_buffer

def _reconstruct_composition_handle_paste(ts, evt, buffer, composition_events, peak_buffer):
    pasted_text = evt.get('pasted_text', '')
    buffer += pasted_text
    if len(buffer) > len(peak_buffer):
        peak_buffer = buffer
    composition_events.append({
        'ts': ts, 'action': 'paste',
        'char': pasted_text, 'buffer': buffer,
    })
    return buffer, composition_events, peak_buffer

def _reconstruct_composition_handle_cut(ts, evt, buffer, composition_events, deleted_chars):
    deleted_text = evt.get('deleted_text', '')
    if deleted_text:
        for i, ch in enumerate(reversed(deleted_text)):
            deleted_chars.append({'char': ch, 'ts': ts, 'pos': max(0, len(buffer) - i - 1)})
    composition_events.append({
        'ts': ts, 'action': 'cut',
        'char': '', 'buffer': '',
        'deleted': deleted_text,
    })
    buffer = ''
    return buffer, composition_events, deleted_chars

def _reconstruct_composition_flush_delete_run(etype, delete_run, insert_after_delete):
    if etype == 'insert' and delete_run and len(insert_after_delete) >= len(delete_run):
        delete_run = []
        insert_after_delete = []
    elif etype not in ('backspace', 'insert') and delete_run:
        delete_run = []
        insert_after_delete = []
    return delete_run, insert_after_delete

def _reconstruct_composition_extract_deleted_words(deleted_chars):
    deleted_words = []
    return deleted_words

def _reconstruct_composition_classify_all_deletions(composition_events):
    typo_corrections = 0
    intentional_deletions = 0
    return typo_corrections, intentional_deletions

def _reconstruct_composition_extract_intent_deletions(composition_events):
    intent_deleted_words = []
    intent_delete_chars = 0
    return intent_deleted_words, intent_delete_chars

def _reconstruct_composition_extract_rewrites(composition_events):
    rewrites = []
    return rewrites

def _reconstruct_composition_compute_stats(events, buffer, peak_buffer, deleted_chars, composition_events, intent_delete_chars):
    timestamps = [e.get('ts', 0) for e in events if e.get('ts')]
    duration_ms = (max(timestamps) - min(timestamps)) if len(timestamps) > 1 else 1
    total_inserts = sum(1 for e in events if e.get('type') in ('insert', 'paste', 'paste_replace'))
    total_deletes = sum(1 for e in events if e.get('type') in
                        ('backspace', 'selection_delete', 'selection_replace', 'cut'))
    total_keys = total_inserts + total_deletes
    chars_per_sec = round(total_inserts / max(duration_ms / 1000, 0.001), 1)
    deletion_ratio = round(total_deletes / max(total_keys, 1), 3)
    intent_deletion_ratio = round(intent_delete_chars / max(total_keys, 1), 3)
    return {
        'total_keys': total_keys,
        'duration_ms': duration_ms,
        'chars_per_sec': chars_per_sec,
        'deletion_ratio': deletion_ratio,
        'intent_deletion_ratio': intent_deletion_ratio,
    }


def _extract_deleted_words(deleted_chars: list) -> list:
    """Group consecutive deleted characters into words."""
    if not deleted_chars:
        return []

    words = []
    current_word = ''
    current_ts = 0
    current_pos = 0

    # Deleted chars come in reverse order (last char deleted first)
    # Group by proximity in time and position
    for i, dc in enumerate(deleted_chars):
        if not current_word:
            current_word = dc['char']
            current_ts = dc['ts']
            current_pos = dc['pos']
        else:
            # Same burst? (within 500ms of previous delete)
            if i > 0 and dc['ts'] - deleted_chars[i-1]['ts'] < 500:
                current_word = dc['char'] + current_word  # prepend (deleting right-to-left)
                current_pos = dc['pos']
            else:
                # Flush current word
                word = current_word.strip()
                if len(word) >= 2:
                    words.append({'word': word, 'ts': current_ts, 'position': current_pos})
                current_word = dc['char']
                current_ts = dc['ts']
                current_pos = dc['pos']

    # Flush last word
    if current_word:
        word = current_word.strip()
        if len(word) >= 2:
            words.append({'word': word, 'ts': current_ts, 'position': current_pos})

    return words


def _extract_rewrites(comp_events: list) -> list:
    """Find rewrite patterns: delete N chars then type N different chars at same position."""
    rewrites = []
    i = 0
    while i < len(comp_events):
        # Find start of a delete run
        if comp_events[i]['action'] != 'delete':
            i += 1
            continue

        # Accumulate delete run
        del_start = i
        deleted_text = ''
        while i < len(comp_events) and comp_events[i]['action'] == 'delete':
            deleted_text = comp_events[i]['char'] + deleted_text  # prepend
            i += 1

        if len(deleted_text) < REWRITE_MIN_CHARS:
            continue

        # Accumulate following insert run
        inserted_text = ''
        while i < len(comp_events) and comp_events[i]['action'] == 'insert':
            inserted_text += comp_events[i]['char']
            i += 1

        if len(inserted_text) >= REWRITE_MIN_CHARS and inserted_text != deleted_text:
            rewrites.append({
                'old': deleted_text,
                'new': inserted_text,
                'ts': comp_events[del_start]['ts'],
                'position': len(comp_events[del_start].get('buffer', '')),
            })

    return rewrites


def _classify_all_deletions(comp_events: list) -> tuple[int, int]:
    """Classify each delete run as typo correction or intentional deletion."""
    typos = 0
    intentional = 0
    i = 0
    while i < len(comp_events):
        if comp_events[i]['action'] != 'delete':
            i += 1
            continue

        del_start = i
        del_count = 0
        while i < len(comp_events) and comp_events[i]['action'] == 'delete':
            del_count += 1
            i += 1

        # Check timing: how long between the last insert before this delete?
        if del_start > 0:
            prev = comp_events[del_start - 1]
            gap = comp_events[del_start]['ts'] - prev['ts']
            if gap < TYPO_WINDOW_MS and del_count <= 3:
                typos += 1
            else:
                intentional += 1
        else:
            intentional += 1

    return typos, intentional


def _extract_intent_deletions(comp_events: list) -> tuple[list, int]:
    """Extract deleted words ONLY from runs of 8+ consecutive backspaces.

    Short runs (1-7) are typo/habit noise. 8+ consecutive backspaces signal
    a genuine line-of-thinking change — the operator started saying X and
    pivoted to Y. These are the real unsaid threads.

    Also counts selection_delete/selection_replace/cut as intent deletions
    since those are always deliberate (you select before deleting).

    Returns:
        (intent_deleted_words, intent_delete_char_count)
    """
    intent_words = []
    intent_chars = 0
    i = 0

    while i < len(comp_events):
        action = comp_events[i]['action']

        if action == 'delete':
            # Accumulate consecutive delete run
            run_start = i
            deleted_text = ''
            while i < len(comp_events) and comp_events[i]['action'] == 'delete':
                deleted_text = comp_events[i]['char'] + deleted_text  # prepend (right-to-left)
                i += 1

            if len(deleted_text) >= INTENT_DELETE_MIN_RUN:
                intent_chars += len(deleted_text)
                word = deleted_text.strip()
                if len(word) >= 2:
                    intent_words.append({
                        'word': word,
                        'ts': comp_events[run_start]['ts'],
                        'position': len(comp_events[run_start].get('buffer', '')),
                        'run_length': len(deleted_text),
                    })

        elif action in ('selection_delete', 'selection_replace', 'cut'):
            # Selection-based deletions are always intentional
            deleted = comp_events[i].get('deleted', '')
            if deleted:
                intent_chars += len(deleted)
                word = deleted.strip()
                if len(word) >= 2:
                    intent_words.append({
                        'word': word,
                        'ts': comp_events[i]['ts'],
                        'position': 0,
                        'run_length': len(deleted),
                    })
            i += 1
        else:
            i += 1

    return intent_words, intent_chars


# ── Cognitive state from composition ─────────────────────────────────────────

def classify_chat_state(comp: dict) -> dict:
    """Classify cognitive state from chat composition analysis.

    Returns:
        {
            'state': str,  # one of the 7 cognitive states
            'confidence': float,
            'signals': dict,  # raw signal values
        }
    """
    dr = comp['deletion_ratio']
    cps = comp['chars_per_sec']
    n_hes = len(comp['hesitation_windows'])
    n_rewrites = len(comp['rewrites'])
    n_deleted_words = len(comp['deleted_words'])
    dur_s = comp['duration_ms'] / 1000

    # WPM approximation (5 chars per word)
    wpm = round((comp['total_keystrokes'] - comp['deleted_chars_total']) / 5
                / max(dur_s / 60, 0.001), 1)

    signals = {
        'deletion_ratio': dr,
        'chars_per_sec': cps,
        'wpm': wpm,
        'hesitation_count': n_hes,
        'rewrite_count': n_rewrites,
        'deleted_word_count': n_deleted_words,
        'intentional_deletions': comp['intentional_deletions'],
        'typo_corrections': comp['typo_corrections'],
    }

    # Classification rules (mirrors adapter_seq001 states)
    if dr > 0.4 and n_hes >= 2:
        state, conf = 'frustrated', min(0.9, 0.5 + dr)
    elif n_rewrites >= 2 and dr > 0.25:
        state, conf = 'restructuring', min(0.85, 0.4 + n_rewrites * 0.15)
    elif n_hes >= 3 and wpm < 30:
        state, conf = 'hesitant', min(0.85, 0.4 + n_hes * 0.1)
    elif cps > 5 and dr < 0.15 and n_hes == 0:
        state, conf = 'flow', min(0.9, 0.5 + cps * 0.05)
    elif cps > 3 and dr < 0.25:
        state, conf = 'focused', min(0.8, 0.4 + cps * 0.1)
    else:
        state, conf = 'neutral', 0.5

    return {'state': state, 'confidence': round(conf, 3), 'signals': signals}


# ── Read and segment OS hook log ─────────────────────────────────────────────

def _read_messages(log_path: Path) -> list[list[dict]]:
    """Split OS hook log into per-message event lists (split on submit/discard).

    Groups ALL keystroke events between submit/discard markers, regardless of
    context tag. Post-filters to keep only messages with meaningful typing
    (>= 5 insert events), which filters editor Enter presses while keeping
    real chat compositions.
    """
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

        # The canonical stroke log now includes both VS Code aggregate events and
        # OS-hook raw key events. Composition replay must only consume raw chat keys.
        if evt.get('source') == 'vscode':
            continue
        if evt.get('type') not in ('insert', 'backspace', 'submit', 'discard'):
            continue
        events.append(evt)

    # Group events between submit/discard markers
    messages = []
    current: list[dict] = []
    for evt in events:
        current.append(evt)
        if evt.get('type') in ('submit', 'discard'):
            if current:
                messages.append(current)
            current = []

    # Post-filter: keep only messages with meaningful typing (not just Enter)
    MIN_INSERTS = 5
    messages = [m for m in messages
                if sum(1 for e in m if e['type'] == 'insert') >= MIN_INSERTS]

    return messages


def analyze_latest_composition(root: Path, n: int = 1) -> list[dict]:
    """Analyze the last N compositions from os_keystrokes.jsonl.

    Returns list of composition analysis dicts, most recent last.
    """
    log_path = root / 'logs' / 'os_keystrokes.jsonl'
    messages = _read_messages(log_path)
    if not messages:
        return []

    results = []
    for msg_events in messages[-n:]:
        comp = reconstruct_composition(msg_events)
        chat_state = classify_chat_state(comp)
        results.append({
            **comp,
            'chat_state': chat_state,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        })

    return results


def analyze_and_log(root: Path) -> dict | None:
    """Analyze latest composition and append to chat_compositions.jsonl.

    Tracks the last-processed submit timestamp to avoid re-logging
    the same composition on every flush cycle.
    """
    log_path = root / 'logs' / 'os_keystrokes.jsonl'
    messages = _read_messages(log_path)
    if not messages:
        return None

    # Find the submit timestamp of the last message
    last_msg = messages[-1]
    submit_ts = None
    for evt in reversed(last_msg):
        if evt.get('type') in ('submit', 'discard'):
            submit_ts = evt.get('ts')
            break

    # Check if we already logged this message
    marker_path = root / 'logs' / '.last_composition_ts'
    if submit_ts and marker_path.exists():
        try:
            prev_ts = int(marker_path.read_text('utf-8').strip())
            if submit_ts <= prev_ts:
                return None  # Already processed
        except (ValueError, OSError):
            pass

    result = reconstruct_composition(last_msg)
    chat_state = classify_chat_state(result)
    result['chat_state'] = chat_state
    result['timestamp'] = datetime.now(timezone.utc).isoformat()

    # Write to log (strip the full composition_events to save space)
    log_entry = {
        'ts': result['timestamp'],
        'final_text': result['final_text'],
        'chat_state': result['chat_state'],
        'deleted_words': result['deleted_words'],
        'intent_deleted_words': result.get('intent_deleted_words', []),
        'rewrites': result['rewrites'],
        'hesitation_windows': result['hesitation_windows'],
        'deletion_ratio': result['deletion_ratio'],
        'intent_deletion_ratio': result.get('intent_deletion_ratio', 0),
        'peak_buffer': result['peak_buffer'],
        'duration_ms': result['duration_ms'],
        'total_keystrokes': result['total_keystrokes'],
        'typo_corrections': result['typo_corrections'],
        'intentional_deletions': result['intentional_deletions'],
    }

    comp_log = root / 'logs' / 'chat_compositions.jsonl'
    comp_log.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(comp_log, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    except OSError:
        pass

    # Update marker so we don't re-log this message
    if submit_ts:
        try:
            marker_path.write_text(str(submit_ts), encoding='utf-8')
        except OSError:
            pass

    return result


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path('.')
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    results = analyze_latest_composition(root, n=n)
    for r in results:
        # Print summary, not full replay
        print(json.dumps({
            'final_text': r['final_text'],
            'chat_state': r['chat_state'],
            'deleted_words': r['deleted_words'],
            'rewrites': r['rewrites'],
            'hesitation_count': len(r['hesitation_windows']),
            'deletion_ratio': r['deletion_ratio'],
            'peak_buffer': r['peak_buffer'],
            'duration_ms': r['duration_ms'],
        }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
