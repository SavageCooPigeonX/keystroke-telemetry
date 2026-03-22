"""dynamic_prompt_seq017_document_analysis_b_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
import json, re, subprocess

def _coaching(root):
    p = root / 'operator_coaching.md'
    if not p.exists(): return []
    text = p.read_text(encoding='utf-8', errors='ignore')
    bullets = []
    for line in text.splitlines():
        m = re.match(r'\s*\*\s*\*\*(.+?)\*\*', line)
        if m: bullets.append(m.group(1).rstrip(':'))
    return bullets[:5]
