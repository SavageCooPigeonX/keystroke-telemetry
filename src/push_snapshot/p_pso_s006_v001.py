"""push_snapshot_seq001_v001_operator_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 22 lines | ~218 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def _load_operator_signal(root: Path) -> dict:
    """Load latest operator signal from push cycle state or prompt telemetry."""
    p = root / 'logs' / 'prompt_telemetry_latest.json'
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text('utf-8'))
        summary = data.get('running_summary', {})
        latest = data.get('latest_prompt', {})
        return {
            'prompt_count': summary.get('total_prompts', 0),
            'avg_wpm': summary.get('avg_wpm', 0),
            'avg_deletion': summary.get('avg_del_ratio', 0),
            'dominant_state': summary.get('dominant_state', 'unknown'),
            'dominant_intent': latest.get('intent', 'unknown'),
        }
    except Exception:
        return {}
