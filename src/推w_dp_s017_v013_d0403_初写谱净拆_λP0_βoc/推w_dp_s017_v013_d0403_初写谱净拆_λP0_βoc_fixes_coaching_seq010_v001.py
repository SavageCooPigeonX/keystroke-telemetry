"""推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_fixes_coaching_seq010_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 010 | VER: v001 | 30 lines | ~315 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json, re, subprocess

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


def _coaching(root):
    p = root / 'operator_coaching.md'
    if not p.exists(): return []
    text = p.read_text(encoding='utf-8', errors='ignore')
    bullets = []
    for line in text.splitlines():
        m = re.match(r'\s*\*\s*\*\*(.+?)\*\*', line)
        if m: bullets.append(m.group(1).rstrip(':'))
    return bullets[:5]
