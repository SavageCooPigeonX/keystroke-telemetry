"""tc_context_seq001_v001_interrogation_seq010_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 010 | VER: v001 | 20 lines | ~178 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re

def _load_context_interrogation_answers(ctx: dict, repo_root: Path) -> None:
    ia = repo_root / 'logs' / 'interrogation_answers.jsonl'
    if not ia.exists():
        return
    try:
        lines = ia.read_text('utf-8', errors='ignore').strip().splitlines()
        ctx['interrogation_answers'] = []
        for line in lines[-10:]:
            entry = json.loads(line)
            ctx['interrogation_answers'].append({
                'module': entry.get('module', ''),
                'answer': entry.get('answer', '')[:200],
            })
    except Exception:
        pass
