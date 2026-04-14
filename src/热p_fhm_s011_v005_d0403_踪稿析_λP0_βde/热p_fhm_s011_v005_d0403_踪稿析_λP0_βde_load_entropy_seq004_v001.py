"""热p_fhm_s011_v005_d0403_踪稿析_λP0_βde_load_entropy_seq004_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 004 | VER: v001 | 20 lines | ~170 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re

def _load_entropy_scores(root: Path) -> dict[str, float]:
    """Load per-module entropy from entropy_map.json."""
    ep = root / 'logs' / 'entropy_map.json'
    if not ep.exists():
        return {}
    try:
        data = json.loads(ep.read_text('utf-8', errors='ignore'))
        result = {}
        for m in data.get('top_entropy_modules', []):
            mod = m.get('module', '')
            if mod:
                result[mod] = m.get('avg_entropy', 0.0)
        return result
    except Exception:
        return {}
