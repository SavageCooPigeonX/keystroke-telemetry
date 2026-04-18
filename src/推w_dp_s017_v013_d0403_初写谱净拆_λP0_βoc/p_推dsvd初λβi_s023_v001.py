"""推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_inject_seq023_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 023 | VER: v001 | 23 lines | ~238 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json, re, subprocess

def inject_task_context(root):
    root = Path(root)
    cp = root / '.github' / 'copilot-instructions.md'
    if not cp.exists(): return False
    block = build_task_context(root)
    original = cp.read_text(encoding='utf-8')
    original_len = len(original)
    text = _strip_task_context_blocks(original)
    idx = _find_task_context_anchor(text)
    if idx >= 0:
        text = text[:idx].rstrip() + '\n\n' + block + '\n\n' + text[idx:].lstrip()
    else:
        text = text.rstrip() + '\n\n---\n\n' + block + '\n'
    # Safety guard: never write if output lost >50% of original content
    # (protects against concurrent writer races nuking the file)
    if original_len > 200 and len(text) < original_len * 0.5:
        return False
    cp.write_text(text, encoding='utf-8')
    return True
