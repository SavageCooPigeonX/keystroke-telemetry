"""tc_context_session_info_seq009_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v001 | 20 lines | ~181 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re

def _load_context_session_info(ctx: dict, repo_root: Path) -> None:
    pj = repo_root / 'logs' / 'prompt_journal.jsonl'
    if not pj.exists():
        return
    try:
        lines = pj.read_text('utf-8', errors='ignore').strip().splitlines()
        last = json.loads(lines[-1]) if lines else {}
        ctx['session_info'] = {
            'session_id': last.get('session_id', '')[:8],
            'session_n': last.get('session_n', 0),
            'intent': last.get('intent', ''),
            'cognitive_state': last.get('cognitive_state', ''),
        }
    except Exception:
        pass
