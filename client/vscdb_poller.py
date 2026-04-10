"""
vscdb_poller.py — Polls VS Code's state.vscdb for chat session data.

Captures:
  - Every submitted prompt (from memento/interactive-session)
  - Session metadata (model, mode, attachments)
  - Draft composition state (from memento/interactive-session-view-copilot)
  - Diffs between polls to detect new prompts and composition changes

Writes to logs/vscdb_drafts.jsonl

Usage: py client/vscdb_poller.py <project_root>
"""
import sqlite3
import json
import sys
import os
import time
import hashlib
from datetime import datetime, timezone

POLL_INTERVAL_S = 0.2          # 200ms — high-fidelity draft capture
SLOW_POLL_INTERVAL_S = 2.0    # 2s for heavy keys (session index, etc.)

# Fast-polled: draft composition (changes every keystroke)
FAST_KEYS = [
    'memento/interactive-session-view-copilot',
]
# Slow-polled: heavier structures that change on submit
SLOW_KEYS = [
    'memento/interactive-session',
    'chat.ChatSessionStore.index',
    'agentSessions.state.cache',
]


def find_vscdb(project_root: str) -> str | None:
    """Find the state.vscdb for the given project root."""
    appdata = os.environ.get('APPDATA', '')
    ws_root = os.path.join(appdata, 'Code', 'User', 'workspaceStorage')
    if not os.path.isdir(ws_root):
        return None
    for d in os.listdir(ws_root):
        ws_json = os.path.join(ws_root, d, 'workspace.json')
        if os.path.exists(ws_json):
            try:
                with open(ws_json, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Match by folder name (last component of project root)
                folder_name = os.path.basename(project_root)
                if folder_name in content:
                    candidate = os.path.join(ws_root, d, 'state.vscdb')
                    if os.path.exists(candidate):
                        return candidate
            except (OSError, json.JSONDecodeError):
                continue
    return None


def read_key(db_path: str, key: str) -> str | None:
    """Read a single key from state.vscdb (reads WAL pages too)."""
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT value FROM ItemTable WHERE key = ?", (key,))
        row = cur.fetchone()
        conn.close()
        if row:
            val = row[0]
            return val.decode('utf-8', errors='replace') if isinstance(val, bytes) else val
    except (sqlite3.Error, OSError):
        pass
    return None


def extract_prompts(session_data: str) -> list[dict]:
    """Extract submitted prompts from memento/interactive-session."""
    try:
        data = json.loads(session_data)
    except json.JSONDecodeError:
        return []
    history = data.get('history', {})
    prompts = []
    for provider, entries in history.items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            prompts.append({
                'provider': provider,
                'text': entry.get('inputText', ''),
                'model': entry.get('selectedModel', {}).get('identifier', ''),
                'mode': entry.get('mode', {}).get('id', ''),
                'attachments': len(entry.get('attachments', [])),
            })
    return prompts


def extract_draft(draft_data: str) -> dict | None:
    """Extract current draft composition from memento/interactive-session-view-copilot."""
    try:
        data = json.loads(draft_data)
    except json.JSONDecodeError:
        return None
    return {
        'input_text': data.get('inputText', ''),
        'model': data.get('selectedModel', {}).get('identifier', ''),
        'mode': data.get('mode', {}).get('id', ''),
        'attachments': len(data.get('attachments', [])),
    }


def hash_val(val: str | None) -> str:
    """Fast hash for diff detection."""
    if val is None:
        return ''
    return hashlib.md5(val.encode('utf-8', errors='replace')).hexdigest()


def _compute_draft_diff(prev: str, new: str) -> dict:
    """Compute character-level diff metrics between draft states."""
    prev_len = len(prev)
    new_len = len(new)
    # Find common prefix
    common_prefix = 0
    for i in range(min(prev_len, new_len)):
        if prev[i] == new[i]:
            common_prefix += 1
        else:
            break
    # Find common suffix (after prefix)
    common_suffix = 0
    for i in range(1, min(prev_len - common_prefix, new_len - common_prefix) + 1):
        if prev[-i] == new[-i]:
            common_suffix += 1
        else:
            break
    chars_deleted = prev_len - common_prefix - common_suffix
    chars_added = new_len - common_prefix - common_suffix
    deleted_text = prev[common_prefix:prev_len - common_suffix] if chars_deleted > 0 else ''
    return {
        'chars_added': chars_added,
        'chars_deleted': chars_deleted,
        'deleted_text': deleted_text[:200],
        'new_len': new_len,
        'prev_len': prev_len,
        'edit_pos': common_prefix,
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'usage: py vscdb_poller.py <project_root>'}))
        sys.exit(1)

    project_root = sys.argv[1]
    db_path = find_vscdb(project_root)

    if not db_path:
        print(json.dumps({'error': 'state.vscdb not found'}))
        sys.exit(1)

    log_dir = os.path.join(project_root, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, 'vscdb_drafts.jsonl')

    # Signal startup
    print(json.dumps({
        'status': 'started',
        'db_path': db_path,
        'pid': os.getpid(),
    }), flush=True)

    # Initial state snapshot
    prev_hashes: dict[str, str] = {}
    prev_prompt_count = 0
    prev_draft_text = ''

    for key in FAST_KEYS + SLOW_KEYS:
        val = read_key(db_path, key)
        prev_hashes[key] = hash_val(val)

    # Extract initial prompt count
    session_val = read_key(db_path, 'memento/interactive-session')
    if session_val:
        prev_prompt_count = len(extract_prompts(session_val))

    draft_val = read_key(db_path, 'memento/interactive-session-view-copilot')
    if draft_val:
        d = extract_draft(draft_val)
        if d:
            prev_draft_text = d['input_text']

    # ── Draft session accumulator ──────────────────────────────────────────
    # Tracks cumulative metrics for the current draft composition session.
    # Resets on submit or abandonment (draft→empty).
    draft_session = {
        'first_change_ts': None,     # when operator started typing this draft
        'last_change_ts': None,      # most recent edit
        'total_chars_added': 0,      # cumulative insertions
        'total_chars_deleted': 0,    # cumulative deletions
        'draft_changes': 0,          # number of poll cycles with changes
        'hesitation_count': 0,       # gaps > 2s between draft changes
        'peak_len': 0,               # max draft length seen
        'deleted_words': [],         # words extracted from deleted text
    }
    HESITATION_MS = 2000  # gap > 2s between changes = hesitation

    def _reset_session():
        draft_session['first_change_ts'] = None
        draft_session['last_change_ts'] = None
        draft_session['total_chars_added'] = 0
        draft_session['total_chars_deleted'] = 0
        draft_session['draft_changes'] = 0
        draft_session['hesitation_count'] = 0
        draft_session['peak_len'] = 0
        draft_session['deleted_words'] = []

    def _extract_deleted_words(text: str) -> list[str]:
        """Extract words from deleted text fragment."""
        return [w for w in text.split() if len(w) >= 3]

    slow_counter = 0
    while True:
        time.sleep(POLL_INTERVAL_S)
        slow_counter += 1

        # Fast poll: draft composition every 200ms
        keys_this_cycle = list(FAST_KEYS)
        # Slow poll: heavy keys every 2s (every 10th cycle)
        if slow_counter >= int(SLOW_POLL_INTERVAL_S / POLL_INTERVAL_S):
            keys_this_cycle.extend(SLOW_KEYS)
            slow_counter = 0

        for key in keys_this_cycle:
            val = read_key(db_path, key)
            h = hash_val(val)

            if h != prev_hashes.get(key, ''):
                prev_hashes[key] = h
                ts = datetime.now(timezone.utc).isoformat()
                now_ms = int(time.time() * 1000)

                if key == 'memento/interactive-session' and val:
                    prompts = extract_prompts(val)
                    new_count = len(prompts)
                    if new_count > prev_prompt_count:
                        for p in prompts[prev_prompt_count:]:
                            # Compute composition time
                            comp_time_ms = None
                            if draft_session['first_change_ts']:
                                comp_time_ms = now_ms - int(
                                    datetime.fromisoformat(
                                        draft_session['first_change_ts']
                                    ).timestamp() * 1000)
                            entry = {
                                'ts': ts,
                                'event': 'prompt_submitted',
                                'source': 'vscdb',
                                **p,
                                # Session-level composition metrics
                                'composition_time_ms': comp_time_ms,
                                'total_chars_added': draft_session['total_chars_added'],
                                'total_chars_deleted': draft_session['total_chars_deleted'],
                                'draft_changes': draft_session['draft_changes'],
                                'hesitation_count': draft_session['hesitation_count'],
                                'peak_draft_len': draft_session['peak_len'],
                                'deletion_ratio': round(
                                    draft_session['total_chars_deleted'] /
                                    max(draft_session['total_chars_added'] +
                                        draft_session['total_chars_deleted'], 1), 3),
                                'deleted_words': draft_session['deleted_words'][-20:],
                            }
                            line = json.dumps(entry, ensure_ascii=False) + '\n'
                            try:
                                with open(log_path, 'a', encoding='utf-8') as f:
                                    f.write(line)
                            except OSError:
                                pass
                        prev_prompt_count = new_count
                        _reset_session()

                elif key == 'memento/interactive-session-view-copilot' and val:
                    draft = extract_draft(val)
                    if draft and draft['input_text'] != prev_draft_text:
                        diff = _compute_draft_diff(prev_draft_text, draft['input_text'])

                        # Detect hesitation (gap > 2s since last change)
                        is_hesitation = False
                        if draft_session['last_change_ts']:
                            last_ms = int(
                                datetime.fromisoformat(
                                    draft_session['last_change_ts']
                                ).timestamp() * 1000)
                            if now_ms - last_ms > HESITATION_MS:
                                is_hesitation = True
                                draft_session['hesitation_count'] += 1

                        # Detect abandonment (had text, now empty, no submit)
                        is_abandon = (
                            len(prev_draft_text) > 5 and
                            len(draft['input_text']) == 0 and
                            draft_session['draft_changes'] > 0
                        )

                        # Update session accumulator
                        if not draft_session['first_change_ts']:
                            draft_session['first_change_ts'] = ts
                        draft_session['last_change_ts'] = ts
                        draft_session['total_chars_added'] += diff['chars_added']
                        draft_session['total_chars_deleted'] += diff['chars_deleted']
                        draft_session['draft_changes'] += 1
                        draft_session['peak_len'] = max(
                            draft_session['peak_len'], diff['new_len'])
                        if diff['deleted_text']:
                            draft_session['deleted_words'].extend(
                                _extract_deleted_words(diff['deleted_text']))

                        entry = {
                            'ts': ts,
                            'event': 'draft_abandoned' if is_abandon else 'draft_changed',
                            'source': 'vscdb',
                            'new_text': draft['input_text'],
                            'prev_text': prev_draft_text,
                            'model': draft['model'],
                            'mode': draft['mode'],
                            # Per-change diff metrics
                            'chars_added': diff['chars_added'],
                            'chars_deleted': diff['chars_deleted'],
                            'deleted_text': diff['deleted_text'],
                            'edit_pos': diff['edit_pos'],
                            'is_hesitation': is_hesitation,
                            # Running session totals
                            'session_chars_added': draft_session['total_chars_added'],
                            'session_chars_deleted': draft_session['total_chars_deleted'],
                            'session_changes': draft_session['draft_changes'],
                        }
                        line = json.dumps(entry, ensure_ascii=False) + '\n'
                        try:
                            with open(log_path, 'a', encoding='utf-8') as f:
                                f.write(line)
                        except OSError:
                            pass

                        if is_abandon:
                            _reset_session()

                        prev_draft_text = draft['input_text']

                elif key == 'chat.ChatSessionStore.index' and val:
                    entry = {
                        'ts': ts,
                        'event': 'session_index_changed',
                        'source': 'vscdb',
                        'data': json.loads(val) if val else None,
                    }
                    line = json.dumps(entry, ensure_ascii=False) + '\n'
                    try:
                        with open(log_path, 'a', encoding='utf-8') as f:
                            f.write(line)
                    except OSError:
                        pass


if __name__ == '__main__':
    main()
