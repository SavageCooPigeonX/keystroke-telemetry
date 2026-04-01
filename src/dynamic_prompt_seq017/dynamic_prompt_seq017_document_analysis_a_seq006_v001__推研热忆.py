"""dynamic_prompt_seq017_document_analysis_a_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
import json, re, subprocess

def _narrative_risks(root):
    d = root / 'docs' / 'push_narratives'
    if not d.exists(): return [], []
    files = sorted(d.glob('*.md'), reverse=True)[:3]
    if not files: return [], []
    watchlist, assumptions = [], []
    for f in files:
        text = f.read_text(encoding='utf-8', errors='ignore')
        for line in text.splitlines():
            l = line.strip()
            if l.upper().startswith('REGRESSION WATCHLIST'):
                watchlist.extend(r.strip() for r in l.split(':', 1)[-1].split(',') if r.strip())
            if 'assumes' in l.lower() and '—' in l and not l.startswith('**'):
                assumptions.append(l[:120])
            elif l.startswith('**') and 'speaks:' in l:
                assumptions.append(l[:120])
            elif l.startswith('**') and 'was touched' in l:
                assumptions.append(l[:120])
    return watchlist[:5], assumptions[:6]


def _self_fix_crit(root):
    d = root / 'docs' / 'self_fix'
    if not d.exists(): return []
    files = sorted(d.glob('*.md'), reverse=True)
    if not files: return []
    lines = files[0].read_text(encoding='utf-8', errors='ignore').splitlines()
    items = []
    for i, line in enumerate(lines):
        if '[CRITICAL]' in line or '[HIGH]' in line:
            sev = '[CRITICAL]' if '[CRITICAL]' in line else '[HIGH]'
            kind = re.sub(r'^.*\]\s*', '', line.strip())
            fline = next((l for l in lines[i+1:i+4] if '**File**' in l), '')
            fname = re.sub(r'.*\*\*File\*\*:\s*', '', fline).strip()
            items.append(f'{sev} {kind}' + (f' in `{fname}`' if fname else ''))
    seen = set()
    return [x for x in items if not (x in seen or seen.add(x))][:5]
