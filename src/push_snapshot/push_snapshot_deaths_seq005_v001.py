"""push_snapshot_deaths_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 19 lines | ~174 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def _load_deaths(root: Path) -> dict:
    p = root / 'execution_death_log.json'
    if not p.exists():
        return {'total': 0, 'by_cause': {}}
    try:
        data = json.loads(p.read_text('utf-8'))
        if not isinstance(data, list):
            return {'total': 0, 'by_cause': {}}
        by_cause: dict[str, int] = {}
        for d in data:
            cause = d.get('cause', 'unknown')
            by_cause[cause] = by_cause.get(cause, 0) + 1
        return {'total': len(data), 'by_cause': by_cause}
    except Exception:
        return {'total': 0, 'by_cause': {}}
