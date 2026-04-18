"""tc_context_seq001_v001_prompts_seq012_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 012 | VER: v001 | 20 lines | ~171 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re

def _load_context_recent_prompts(ctx: dict, repo_root: Path) -> None:
    journal = repo_root / 'logs' / 'prompt_journal.jsonl'
    if not journal.exists():
        return
    try:
        lines = journal.read_text('utf-8', errors='ignore').strip().splitlines()
        ctx['recent_prompts'] = []
        for line in lines[-5:]:
            entry = json.loads(line)
            ctx['recent_prompts'].append({
                'msg': entry.get('msg', '')[:300],
                'intent': entry.get('intent', ''),
            })
    except Exception:
        pass
