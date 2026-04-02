"""self_fix_seq013_scan_query_noise_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v002 | 26 lines | ~237 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: organism_health_system
# LAST:   2026-03-29 @ 1f4291d
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re

def _scan_query_noise(root: Path) -> list[dict]:
    """Detect poisoned query_memory entries."""
    problems = []
    qm_path = root / 'query_memory.json'
    if not qm_path.exists():
        return problems
    try:
        raw = json.loads(qm_path.read_text('utf-8'))
        entries = raw.get('entries', raw.get('queries', []))
        noise = [e for e in entries
                 if isinstance(e, dict) and '(background)' in str(e.get('text', e.get('query_text', '')))]
        if noise:
            problems.append({
                'type': 'query_noise',
                'count': len(noise),
                'severity': 'high',
                'fix': 'Filter "(background)" queries in extension flush — use active filename instead',
            })
    except Exception:
        pass
    return problems
