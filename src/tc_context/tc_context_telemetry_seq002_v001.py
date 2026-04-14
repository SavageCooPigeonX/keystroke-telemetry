"""tc_context_telemetry_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 21 lines | ~190 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re

def _load_context_telemetry(ctx: dict, repo_root: Path) -> None:
    telem = repo_root / 'logs' / 'prompt_telemetry_latest.json'
    if not telem.exists():
        return
    try:
        t = json.loads(telem.read_text('utf-8', errors='ignore'))
        ctx['hot_modules'] = t.get('hot_modules', [])[:5]
        rs = t.get('running_summary', {})
        ctx['operator_state'] = {
            'dominant': rs.get('dominant_state', 'unknown'),
            'states': rs.get('state_distribution', {}),
            'avg_wpm': rs.get('avg_wpm'),
            'baselines': rs.get('baselines', {}),
        }
    except Exception:
        pass
