"""
chat_response_reader_seq001_v001.py — Reads Copilot chat responses from VS Code chatSessions storage.

Reads the chatSessions JSONL file in workspaceStorage to extract prompt→response
pairs WITHOUT requiring @pigeon invocation. Works on any regular Copilot chat.

Usage:
    from client.chat_response_reader_seq001_v001_seq001_v001 import read_recent_responses
    pairs = read_recent_responses(project_root, limit=5)
    # Returns: [{"prompt": "...", "response": "...", "ts": "...", "request_idx": N}, ...]
"""
import json
import os
import hashlib
from datetime import datetime, timezone


def _normalize_text(text: str, limit: int) -> str:
    if not isinstance(text, str):
        text = str(text or '')
    return text.replace('\r\n', '\n').strip()[:limit]


def _fingerprint_response(prompt: str, response: str) -> str:
    payload = f'{_normalize_text(prompt, 500)}\n\x1f{_normalize_text(response, 5000)}'
    return hashlib.sha1(payload.encode('utf-8', errors='replace')).hexdigest()[:20]


def _build_log_entry(pair: dict, session_file: str | None) -> dict:
    prompt = _normalize_text(pair.get('prompt', ''), 500)
    response = _normalize_text(pair.get('response', ''), 5000)
    request_idx = pair.get('request_idx', -1)
    try:
        request_idx = int(request_idx)
    except (TypeError, ValueError):
        request_idx = -1
    session_id = ''
    if session_file:
        session_id = os.path.splitext(os.path.basename(session_file))[0]
    fingerprint = _fingerprint_response(prompt, response)
    response_id = f'chat:{session_id}:{request_idx}' if session_id and request_idx >= 0 else f'chat:{fingerprint}'
    return {
        'ts': pair.get('ts') or datetime.now(timezone.utc).isoformat(),
        'prompt': prompt,
        'response': response,
        'source': 'chat_session_auto',
        'capture_surface': 'vscode_chat',
        'schema_version': 2,
        'session_id': session_id,
        'request_idx': request_idx,
        'response_id': response_id,
        'response_fingerprint': fingerprint,
    }


def _find_chat_sessions_dir(project_root: str) -> str | None:
    """Find the chatSessions directory in VS Code workspaceStorage for this project."""
    appdata = os.environ.get('APPDATA', '')
    ws_root = os.path.join(appdata, 'Code', 'User', 'workspaceStorage')
    if not os.path.isdir(ws_root):
        return None
    folder_name = os.path.basename(os.path.abspath(project_root))
    for d in os.listdir(ws_root):
        ws_json = os.path.join(ws_root, d, 'workspace.json')
        if os.path.exists(ws_json):
            try:
                with open(ws_json, 'r', encoding='utf-8') as f:
                    content = f.read()
                if folder_name in content:
                    sessions_dir = os.path.join(ws_root, d, 'chatSessions')
                    if os.path.isdir(sessions_dir):
                        return sessions_dir
            except (OSError, json.JSONDecodeError):
                continue
    return None


def _find_latest_session_file(sessions_dir: str) -> str | None:
    """Find the most recently modified .jsonl file in chatSessions."""
    best_path, best_mtime = None, 0
    for fname in os.listdir(sessions_dir):
        if fname.endswith('.jsonl'):
            fpath = os.path.join(sessions_dir, fname)
            mtime = os.path.getmtime(fpath)
            if mtime > best_mtime:
                best_mtime = mtime
                best_path = fpath
    return best_path


def _tail_read(filepath: str, tail_bytes: int = 10_000_000) -> list[str]:
    """Read the last tail_bytes of a file and return complete lines."""
    fsize = os.path.getsize(filepath)
    offset = max(0, fsize - tail_bytes)
    with open(filepath, 'rb') as f:
        if offset > 0:
            f.seek(offset)
            f.readline()  # skip partial first line
        data = f.read()
    return data.decode('utf-8', errors='replace').splitlines(keepends=True)


def _extract_pairs(lines: list[str]) -> list[dict]:
    """Parse JSONL lines and extract prompt→response pairs.

    Strategy: track the order of request entries to determine their index.
    Each k=['requests'] entry appends to the requests array, and the Nth
    unique request (by requestId) maps to index N.  We also directly pick
    up request indices from response/result/modelState entries.
    """
    # First pass: collect request entries with their timestamps and prompts
    request_entries = []  # ordered list of {"requestId", "prompt", "ts"}
    responses = {}        # idx -> [text_parts]

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue

        k = obj.get('k', [])
        v = obj.get('v')

        # New request entry: k = ['requests'], v = [{requestId, message, timestamp...}]
        if k == ['requests'] and isinstance(v, list) and v:
            req = v[0]
            msg = req.get('message', {})
            prompt_text = msg.get('text', '') if isinstance(msg, dict) else ''
            if prompt_text.startswith('@agent Continue'):
                continue
            rid = req.get('requestId', '')
            ts = req.get('timestamp', 0)
            if rid and prompt_text:
                request_entries.append({'requestId': rid, 'prompt': prompt_text, 'ts': ts})

        # Response chunk: k = ['requests', N, 'response']
        if (len(k) == 3 and k[0] == 'requests' and isinstance(k[1], int)
                and k[2] == 'response' and isinstance(v, list)):
            idx = k[1]
            if idx not in responses:
                responses[idx] = []
            for part in v:
                if isinstance(part, dict) and 'value' in part and 'kind' not in part:
                    responses[idx].append(part['value'])

    # Match: we know request entries are in order.  The last N entries
    # in request_entries correspond to the highest N indices.  We can figure
    # out the mapping by looking at what response indices exist.
    # The total request count across the whole file determines the current max index.
    # We'll match from the end.
    max_resp_idx = max(responses.keys()) if responses else -1
    if max_resp_idx < 0:
        return []

    # Build pairs: for each response idx, try to find the matching request
    # by aligning the request_entries list to the known indices.
    # If we have request_entries with the last N entries, and the highest
    # known index is max_resp_idx, then the last request entry corresponds
    # to max_resp_idx (approximately — may be off by continuation prompts).
    # A simpler approach: use requestId matching from the request entry's
    # 'response' field or timestamp proximity.

    # Build a ts→prompt map from request entries
    ts_to_prompt = {}
    for re in request_entries:
        ts_to_prompt[re['ts']] = re['prompt']

    pairs = []
    for idx in sorted(responses.keys()):
        resp_text = ''.join(responses[idx])
        if not resp_text.strip():
            continue
        pairs.append({
            'request_idx': idx,
            'response': resp_text[:5000],
        })

    # Now try to pair prompts.  Read request entries in the original file
    # to find which request_entry maps to which index.  The simplest
    # heuristic: scan lines again and track a running request counter.
    req_counter = 0
    req_idx_map = {}  # idx -> {"prompt", "ts"}
    last_req_entry = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        k = obj.get('k', [])
        v = obj.get('v')

        # When we see a request with modelState for idx N, and the previous
        # request entry is still pending, we know it maps to idx N.
        if k == ['requests'] and isinstance(v, list) and v:
            req = v[0]
            msg = req.get('message', {})
            prompt_text = msg.get('text', '') if isinstance(msg, dict) else ''
            ts = req.get('timestamp', 0)
            if prompt_text and not prompt_text.startswith('@agent Continue'):
                last_req_entry = {'prompt': prompt_text, 'ts': ts}

        # When we see the first response or result for an idx,
        # the last_req_entry is its source
        if (len(k) == 3 and k[0] == 'requests' and isinstance(k[1], int)
                and k[2] in ('response', 'result', 'modelState')):
            idx = k[1]
            if idx not in req_idx_map and last_req_entry:
                req_idx_map[idx] = last_req_entry
                last_req_entry = None

    # Attach prompts to pairs
    for p in pairs:
        idx = p['request_idx']
        if idx in req_idx_map:
            p['prompt'] = req_idx_map[idx]['prompt']
            p['ts'] = req_idx_map[idx]['ts']
        else:
            p['prompt'] = ''
            p['ts'] = 0

    return pairs


def read_recent_responses(project_root: str, limit: int = 5) -> list[dict]:
    """
    Read the last `limit` complete prompt→response pairs from VS Code's
    chatSessions storage. Works automatically — no @pigeon needed.

    Returns list of dicts with canonical response identity fields.
    """
    sessions_dir = _find_chat_sessions_dir(project_root)
    if not sessions_dir:
        return []

    session_file = _find_latest_session_file(sessions_dir)
    if not session_file:
        return []

    lines = _tail_read(session_file)
    pairs = _extract_pairs(lines)

    # Return last N pairs with non-empty responses, formatted
    result = []
    for p in pairs[-(limit * 3):]:  # over-fetch then filter
        if p.get('response', '').strip():
            ts_str = ''
            if p.get('ts'):
                try:
                    ts_str = datetime.fromtimestamp(
                        p['ts'] / 1000, tz=timezone.utc
                    ).isoformat()
                except (OSError, ValueError):
                    pass
            result.append(_build_log_entry({
                'prompt': p.get('prompt', ''),
                'response': p['response'],
                'ts': ts_str,
                'request_idx': p.get('request_idx', -1),
            }, session_file))

    return result[-limit:]


def sync_to_log(project_root: str, limit: int = 5) -> int:
    """
    Read recent responses and append any NEW ones to logs/ai_responses.jsonl.
    Returns count of new entries written. Deduplicates by canonical response ID
    and prompt→response fingerprint across capture sources.
    """
    pairs = read_recent_responses(project_root, limit=limit)
    if not pairs:
        return 0

    log_path = os.path.join(project_root, 'logs', 'ai_responses.jsonl')
    existing_ids = set()
    existing_fingerprints = set()
    existing_session_keys = set()
    if os.path.exists(log_path):
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get('response_id'):
                            existing_ids.add(entry['response_id'])
                        fingerprint = entry.get('response_fingerprint')
                        if not fingerprint and entry.get('response'):
                            fingerprint = _fingerprint_response(
                                entry.get('prompt', ''), entry.get('response', ''),
                            )
                        if fingerprint:
                            existing_fingerprints.add(fingerprint)
                        session_id = str(entry.get('session_id') or '')
                        request_idx = entry.get('request_idx', -1)
                        try:
                            request_idx = int(request_idx)
                        except (TypeError, ValueError):
                            request_idx = -1
                        if session_id and request_idx >= 0:
                            existing_session_keys.add((session_id, request_idx))
                    except json.JSONDecodeError:
                        continue
        except OSError:
            pass

    written = 0
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, 'a', encoding='utf-8') as f:
        for p in pairs:
            response_id = p.get('response_id', '')
            fingerprint = p.get('response_fingerprint', '')
            session_key = (p.get('session_id', ''), p.get('request_idx', -1))
            if (
                response_id in existing_ids
                or fingerprint in existing_fingerprints
                or session_key in existing_session_keys
            ):
                continue
            f.write(json.dumps(p) + '\n')
            if response_id:
                existing_ids.add(response_id)
            if fingerprint:
                existing_fingerprints.add(fingerprint)
            if p.get('session_id') and p.get('request_idx', -1) >= 0:
                existing_session_keys.add(session_key)
            written += 1

    return written


if __name__ == '__main__':
    import sys
    root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    pairs = read_recent_responses(root, limit=5)
    print(f'Found {len(pairs)} recent response(s):')
    for p in pairs:
        prompt_preview = p['prompt'][:80].replace('\n', ' ')
        resp_preview = p['response'][:100].replace('\n', ' ')
        print(f'  [{p["request_idx"]}] {prompt_preview}')
        print(f'       -> {resp_preview}...')
    # Also sync to log
    n = sync_to_log(root, limit=5)
    print(f'\nSynced {n} new entries to logs/ai_responses.jsonl')
