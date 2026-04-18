"""热p_fhm_s011_v005_d0403_踪稿析_λP0_βde_load_heat_map_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 26 lines | ~191 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re

def load_heat_map(root: Path) -> dict:
    """Load file heat map → sorted list for coaching prompt."""
    heat_path = root / HEAT_STORE
    if not heat_path.exists():
        return {}
    try:
        heat = json.loads(heat_path.read_text('utf-8'))
    except Exception:
        return {}

    hot_files = [
        {'module': name, 'heat': d['heat'],
         'touches': d['touch_score'], 'entropy': d['entropy']}
        for name, d in heat.items()
    ]
    hot_files.sort(key=lambda x: x['heat'], reverse=True)

    return {
        'modules_tracked': len(heat),
        'hot_files': hot_files[:8],
    }
