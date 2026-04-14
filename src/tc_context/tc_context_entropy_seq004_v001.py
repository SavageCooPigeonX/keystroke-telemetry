"""tc_context_entropy_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 21 lines | ~177 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re

def _load_context_entropy(ctx: dict, repo_root: Path) -> None:
    emap = repo_root / 'logs' / 'entropy_map.json'
    if not emap.exists():
        return
    try:
        em = json.loads(emap.read_text('utf-8', errors='ignore'))
        ctx['entropy'] = {
            'global': em.get('global_avg_entropy', 0),
            'high_pct': em.get('high_entropy_pct', 0),
            'hotspots': [
                {'mod': m['module'], 'H': round(m['avg_entropy'], 3)}
                for m in em.get('top_entropy_modules', [])[:6]
            ],
        }
    except Exception:
        pass
