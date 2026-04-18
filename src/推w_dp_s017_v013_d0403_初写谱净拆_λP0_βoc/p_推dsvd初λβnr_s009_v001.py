"""推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_narrative_risks_seq009_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v001 | 22 lines | ~261 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
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
