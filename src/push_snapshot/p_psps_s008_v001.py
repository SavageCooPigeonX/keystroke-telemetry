"""push_snapshot_seq001_v001_probe_state_seq008_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 008 | VER: v001 | 33 lines | ~297 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def _load_probe_state(root: Path) -> dict:
    state_dir = root / 'logs' / 'module_state'
    if not state_dir.exists():
        return {'modules_probed': 0, 'total_convos': 0, 'total_intents': 0,
                'total_pain': 0, 'avg_engagement': 0}
    total_convos = 0
    total_intents = 0
    total_pain = 0
    engagement_sum = 0.0
    count = 0
    for f in state_dir.glob('*.json'):
        try:
            s = json.loads(f.read_text('utf-8'))
            convos = s.get('conversation_count', 0)
            if convos > 0:
                count += 1
                total_convos += convos
                total_intents += len(s.get('extracted_intents', []))
                total_pain += len(s.get('pain_points', []))
                engagement_sum += s.get('engagement_score', 0)
        except Exception:
            continue
    return {
        'modules_probed': count,
        'total_convos': total_convos,
        'total_intents': total_intents,
        'total_pain': total_pain,
        'avg_engagement': round(engagement_sum / max(count, 1), 3),
    }
