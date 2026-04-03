"""u_pe_s024_v004_d0403_λP0_βoc_cognitive_state_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

def _cognitive_state(root: Path) -> dict:
    snap = _jload(root / 'logs' / 'prompt_telemetry_latest.json')
    if not snap: return {}
    signals = snap.get('signals', {})
    summary = snap.get('running_summary', {})
    return {
        'state': summary.get('dominant_state', 'unknown'),
        'wpm': signals.get('wpm', 0),
        'del_ratio': signals.get('deletion_ratio', 0),
        'hes': signals.get('hesitation_count', 0),
    }
