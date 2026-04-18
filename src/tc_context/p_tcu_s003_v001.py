"""tc_context_seq001_v001_unsaid_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 18 lines | ~162 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re

def _load_context_unsaid_threads(ctx: dict, repo_root: Path) -> None:
    unsaid = repo_root / 'logs' / 'unsaid_reconstructions.jsonl'
    if not unsaid.exists():
        return
    try:
        lines = unsaid.read_text('utf-8', errors='ignore').strip().splitlines()
        ctx['unsaid_threads'] = []
        for line in lines[-5:]:
            entry = json.loads(line)
            ctx['unsaid_threads'].append(
                entry.get('reconstructed', entry.get('deleted', ''))[:200])
    except Exception:
        pass
