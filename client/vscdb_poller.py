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

POLL_INTERVAL_S = 2.0
KEYS_TO_WATCH = [
    'memento/interactive-session',
    'memento/interactive-session-view-copilot',
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
    """Read a single key from state.vscdb (read-only)."""
    try:
        conn = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
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

    for key in KEYS_TO_WATCH:
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

    while True:
        time.sleep(POLL_INTERVAL_S)

        for key in KEYS_TO_WATCH:
            val = read_key(db_path, key)
            h = hash_val(val)

            if h != prev_hashes.get(key, ''):
                prev_hashes[key] = h
                ts = datetime.now(timezone.utc).isoformat()

                if key == 'memento/interactive-session' and val:
                    prompts = extract_prompts(val)
                    new_count = len(prompts)
                    if new_count > prev_prompt_count:
                        # New prompts submitted
                        for p in prompts[prev_prompt_count:]:
                            entry = {
                                'ts': ts,
                                'event': 'prompt_submitted',
                                'source': 'vscdb',
                                **p,
                            }
                            line = json.dumps(entry, ensure_ascii=False) + '\n'
                            try:
                                with open(log_path, 'a', encoding='utf-8') as f:
                                    f.write(line)
                            except OSError:
                                pass
                        prev_prompt_count = new_count

                elif key == 'memento/interactive-session-view-copilot' and val:
                    draft = extract_draft(val)
                    if draft and draft['input_text'] != prev_draft_text:
                        entry = {
                            'ts': ts,
                            'event': 'draft_changed',
                            'source': 'vscdb',
                            'new_text': draft['input_text'],
                            'prev_text': prev_draft_text,
                            'model': draft['model'],
                            'mode': draft['mode'],
                        }
                        line = json.dumps(entry, ensure_ascii=False) + '\n'
                        try:
                            with open(log_path, 'a', encoding='utf-8') as f:
                                f.write(line)
                        except OSError:
                            pass
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
