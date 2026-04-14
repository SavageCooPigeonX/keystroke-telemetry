"""git_plugin_operator_history_seq009_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v001 | 19 lines | ~160 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re

def _load_operator_history(root: Path) -> list:
    """Extract message history from operator_profile.md DATA block."""
    prof_path = root / 'operator_profile.md'
    if not prof_path.exists():
        return []
    try:
        text = prof_path.read_text(encoding='utf-8')
        m = re.search(r'<!--\s*DATA\s*(.*?)\s*DATA\s*-->', text, re.DOTALL)
        if m:
            data = json.loads(m.group(1).strip())
            return data.get('history', [])
    except Exception:
        pass
    return []
