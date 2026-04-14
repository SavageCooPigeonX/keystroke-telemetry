"""推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_dossier_seq016_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 016 | VER: v001 | 19 lines | ~223 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
import json, re, subprocess

def _active_dossier_signal(root):
    """Read routing signal from enricher. Returns (confidence, focus_modules, focus_bugs)."""
    p = root / 'logs' / 'active_dossier.json'
    if not p.exists(): return 0.0, [], []
    try:
        d = json.loads(p.read_text('utf-8', errors='ignore'))
        # Stale check: ignore signals older than 5 minutes
        ts = d.get('ts', '')
        if ts:
            from datetime import datetime, timezone
            age = (datetime.now(timezone.utc) - datetime.fromisoformat(ts)).total_seconds()
            if age > 300: return 0.0, [], []
        return d.get('confidence', 0.0), d.get('focus_modules', []), d.get('focus_bugs', [])
    except Exception:
        return 0.0, [], []
