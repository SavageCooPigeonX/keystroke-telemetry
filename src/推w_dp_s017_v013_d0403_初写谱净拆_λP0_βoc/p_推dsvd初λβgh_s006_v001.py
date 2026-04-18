"""推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_git_history_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 35 lines | ~374 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json, re, subprocess

def _profile_history(root):
    p = root / 'operator_profile.md'
    if not p.exists(): return []
    m = re.search(r'<!--\s*\n?DATA\s*\n(.*?)\nDATA\s*\n-->',
                  p.read_text(encoding='utf-8', errors='ignore'), re.DOTALL)
    if not m: return []
    try: return json.loads(m.group(1).strip()).get('history', [])
    except Exception: return []


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
