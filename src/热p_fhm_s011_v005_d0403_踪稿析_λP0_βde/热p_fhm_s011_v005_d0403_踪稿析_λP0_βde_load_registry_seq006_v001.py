"""热p_fhm_s011_v005_d0403_踪稿析_λP0_βde_load_registry_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 25 lines | ~227 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re

def load_registry_churn(root: Path) -> list[dict]:
    """Return top-churn modules from pigeon_registry for heat enrichment."""
    reg_path = root / 'pigeon_registry.json'
    if not reg_path.exists():
        return []
    try:
        reg = json.loads(reg_path.read_text('utf-8'))
    except Exception:
        return []
    files = reg.get('files', [])
    if not isinstance(files, list):
        files = [v for v in reg.values() if isinstance(v, dict)]
    entries = [
        {'module': e.get('name', ''), 'ver': e.get('ver', 1),
         'desc': e.get('desc', ''), 'tokens': e.get('tokens', 0)}
        for e in files
        if e.get('ver', 1) >= HIGH_VER_THRESH
    ]
    entries.sort(key=lambda x: x['ver'], reverse=True)
    return entries[:8]
