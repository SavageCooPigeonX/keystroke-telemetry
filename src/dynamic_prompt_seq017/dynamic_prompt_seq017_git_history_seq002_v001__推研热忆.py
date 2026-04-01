"""dynamic_prompt_seq017_git_history_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
import json, re, subprocess

def _commits(root, n=8):
    try:
        r = subprocess.run(['git', 'log', f'-{n}', '--pretty=format:%h|%s'],
                           capture_output=True, text=True, cwd=str(root), timeout=5)
        return [{'hash': p[0], 'msg': p[1]} for line in r.stdout.strip().splitlines()
                if len(p := line.split('|', 1)) == 2]
    except Exception: return []


def _task_focus(commits):
    msgs = [c['msg'] for c in commits[:5] if '[pigeon-auto]' not in c['msg']]
    if not msgs: return 'unknown'
    w = ' '.join(msgs).lower()
    for kw, label in [
        (('fix', 'bug', 'broken', 'error'), 'debugging / fixing'),
        (('feat', 'add', 'build', 'implement'), 'building new features'),
        (('refactor', 'clean', 'rename', 'split'), 'refactoring / restructuring'),
        (('doc', 'readme', 'manifest'), 'documentation / organization'),
        (('test', 'verify', 'check'), 'testing / validation'),
    ]:
        if any(k in w for k in kw): return label
    return msgs[0][:50]
