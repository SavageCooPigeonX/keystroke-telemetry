"""tc_context_seq001_v001_session_chat_seq013_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 013 | VER: v001 | 28 lines | ~295 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re

def _load_context_session_chat(ctx: dict, repo_root: Path) -> None:
    cc = repo_root / 'logs' / 'chat_compositions.jsonl'
    if not cc.exists():
        return
    try:
        lines = cc.read_text('utf-8', errors='ignore').strip().splitlines()
        ctx['session_messages'] = []
        for line in lines[-5:]:
            entry = json.loads(line)
            text_snip = entry.get('final_text', '')[:80]
            cs = entry.get('chat_state', {})
            state = cs.get('state', 'unknown') if isinstance(cs, dict) else 'unknown'
            deleted = entry.get('deleted_words', [])
            rewrites = entry.get('rewrite_chains', [])
            ctx['session_messages'].append({
                'text': text_snip,
                'state': state,
                'del_ratio': entry.get('deletion_ratio', 0),
                'deleted_words': deleted[-6:] if deleted else [],
                'rewrites': [r[:80] if isinstance(r, str) else r for r in (rewrites[-3:] if rewrites else [])],
            })
    except Exception:
        pass
