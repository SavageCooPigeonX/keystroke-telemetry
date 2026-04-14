"""tc_context_heatmap_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 23 lines | ~212 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re

def _load_context_heat_map(ctx: dict, repo_root: Path) -> None:
    fhm = repo_root / 'file_heat_map.json'
    if not fhm.exists():
        return
    try:
        hm = json.loads(fhm.read_text('utf-8', errors='ignore'))
        heat = []
        for mod, data in hm.items():
            h = data.get('heat', 0)
            if h > 0:
                heat.append({'mod': mod, 'heat': round(h, 3),
                             'touches': data.get('touch_score', 0),
                             'entropy': data.get('entropy', 0),
                             'n': round(data.get('touch_score', 0))})
        heat.sort(key=lambda x: x['heat'], reverse=True)
        ctx['heat_map'] = heat[:8]
    except Exception:
        pass
