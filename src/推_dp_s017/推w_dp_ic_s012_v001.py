"""dynamic_prompt_seq017_inject_context_seq012_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json, re, subprocess

def inject_task_context(root):
    root = Path(root)
    cp = root / '.github' / 'copilot-instructions.md'
    if not cp.exists(): return False
    block = build_task_context(root)
    text = cp.read_text(encoding='utf-8')
    pat = re.compile(
        r'(?ms)^\s*<!-- pigeon:task-context -->\s*$\n.*?^\s*<!-- /pigeon:task-context -->\s*$',
    )
    if pat.search(text):
        text = pat.sub(block, text)
    else:
        idx = text.find('<!-- pigeon:operator-state -->')
        if idx >= 0: text = text[:idx] + block + '\n\n' + text[idx:]
        else: text = text.rstrip() + '\n\n---\n\n' + block + '\n'
    cp.write_text(text, encoding='utf-8')
    return True
