"""Task queue — Copilot-driven task tracking linked to MANIFEST.md entries."""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──

import json, re
from pathlib import Path
from datetime import datetime, timezone

_QUEUE_FILE = 'task_queue.json'
_EMPTY = {"tasks": [], "next_id": 1}


def _load(root: Path) -> dict:
    p = root / _QUEUE_FILE
    if not p.exists(): return dict(_EMPTY)
    try: return json.loads(p.read_text(encoding='utf-8'))
    except Exception: return dict(_EMPTY)


def _save(root: Path, q: dict) -> None:
    (root / _QUEUE_FILE).write_text(
        json.dumps(q, indent=2, ensure_ascii=False), encoding='utf-8')


def add_task(root, title: str, intent: str = '', stage: str = 'pending',
             focus_files: list = None, manifest_ref: str = '') -> str:
    root = Path(root)
    q = _load(root)
    tid = f'tq-{q["next_id"]:03d}'
    q['tasks'].append({
        'id': tid, 'title': title, 'status': 'pending',
        'intent': intent, 'stage': stage,
        'focus_files': focus_files or [],
        'manifest_ref': manifest_ref,
        'created_ts': datetime.now(timezone.utc).isoformat(),
        'completed_ts': None, 'commit': None,
    })
    q['next_id'] += 1
    _save(root, q)
    return tid


def mark_done(root, task_id: str, commit: str = '') -> bool:
    root = Path(root)
    q = _load(root)
    for t in q['tasks']:
        if t['id'] == task_id:
            t['status'] = 'done'
            t['completed_ts'] = datetime.now(timezone.utc).isoformat()
            t['commit'] = commit
            _save(root, q)
            return True
    return False


def mark_in_progress(root, task_id: str) -> bool:
    root = Path(root)
    q = _load(root)
    for t in q['tasks']:
        if t['id'] == task_id:
            t['status'] = 'in_progress'
            _save(root, q)
            return True
    return False


def _seed_from_self_fix(root: Path, q: dict) -> None:
    """Auto-add CRITICAL self-fix items as pending tasks if not already queued."""
    d = root / 'docs' / 'self_fix'
    if not d.exists(): return
    files = sorted(d.glob('*.md'), reverse=True)
    if not files: return
    existing = {t['title'] for t in q['tasks']}
    lines = files[0].read_text(encoding='utf-8', errors='ignore').splitlines()
    for i, line in enumerate(lines):
        if '[CRITICAL]' not in line: continue
        kind = re.sub(r'^.*\]\s*', '', line.strip())
        fline = next((l for l in lines[i+1:i+4] if '**File**' in l), '')
        fname = re.sub(r'.*\*\*File\*\*:\s*', '', fline).strip()
        title = f'Fix {kind}' + (f' in `{fname}`' if fname else '')
        if title in existing: continue
        q['tasks'].append({
            'id': f'tq-{q["next_id"]:03d}', 'title': title,
            'status': 'pending', 'intent': 'self_fix', 'stage': 'debugging',
            'focus_files': [fname] if fname else [], 'manifest_ref': '',
            'created_ts': datetime.now(timezone.utc).isoformat(),
            'completed_ts': None, 'commit': None,
        })
        q['next_id'] += 1
        existing.add(title)


def build_task_queue_block(root) -> str:
    root = Path(root)
    q = _load(root)
    _seed_from_self_fix(root, q)
    _save(root, q)
    tasks = q.get('tasks', [])
    in_prog = [t for t in tasks if t['status'] == 'in_progress']
    pending = [t for t in tasks if t['status'] == 'pending']
    done = [t for t in tasks if t['status'] == 'done'][-3:]

    L = ['<!-- pigeon:task-queue -->', '## Active Task Queue', '',
         '*Copilot manages this queue. To complete a task: update the referenced '
         'MANIFEST.md, then call `mark_done(root, task_id)` in `task_queue_seq018`.*', '']

    if in_prog:
        L.append('### In Progress')
        for t in in_prog:
            ff = ', '.join(f'`{f}`' for f in t['focus_files']) if t['focus_files'] else ''
            L.append(f'- [ ] `{t["id"]}` **{t["title"]}**'
                     + (f' | stage: {t["stage"]}' if t['stage'] else '')
                     + (f' | focus: {ff}' if ff else ''))
            if t.get('manifest_ref'):
                L.append(f'  → [{t["manifest_ref"]}]({t["manifest_ref"]})')
        L.append('')

    if pending:
        L.append('### Pending')
        for t in pending[:6]:
            ff = ', '.join(f'`{f}`' for f in t['focus_files']) if t['focus_files'] else ''
            L.append(f'- [ ] `{t["id"]}` **{t["title"]}**'
                     + (f' | stage: {t["stage"]}' if t['stage'] else '')
                     + (f' | focus: {ff}' if ff else ''))
            if t.get('manifest_ref'):
                L.append(f'  → [{t["manifest_ref"]}]({t["manifest_ref"]})')
        if len(pending) > 6:
            L.append(f'*…and {len(pending) - 6} more in `task_queue.json`*')
        L.append('')

    if done:
        L.append('### Completed (last 3)')
        for t in done:
            L.append(f'- [x] `{t["id"]}` **{t["title"]}**'
                     + (f' | commit: `{t["commit"]}`' if t.get('commit') else ''))
        L.append('')

    if not in_prog and not pending:
        L += ['*Queue empty — add tasks via `add_task()` or they auto-seed from self-fix.*', '']

    L.append('<!-- /pigeon:task-queue -->')
    return '\n'.join(L)


def inject_task_queue(root) -> bool:
    root = Path(root)
    cp = root / '.github' / 'copilot-instructions.md'
    if not cp.exists(): return False
    block = build_task_queue_block(root)
    text = cp.read_text(encoding='utf-8')
    pat = re.compile(r'<!-- pigeon:task-queue -->.*?<!-- /pigeon:task-queue -->', re.DOTALL)
    if pat.search(text):
        text = pat.sub(block, text)
    else:
        # Insert after task-context block
        idx = text.find('<!-- /pigeon:task-context -->')
        if idx >= 0:
            ins = idx + len('<!-- /pigeon:task-context -->')
            text = text[:ins] + '\n\n' + block + text[ins:]
        else:
            text = text.rstrip() + '\n\n---\n\n' + block + '\n'
    cp.write_text(text, encoding='utf-8')
    return True


if __name__ == '__main__':
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    print(build_task_queue_block(root))
    inject_task_queue(root)
