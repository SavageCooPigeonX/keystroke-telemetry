"""测p_rwd_s009_v006_d0403_译改名踪_λP0_βde_record_rework_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 005 | VER: v001 | 34 lines | ~314 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
import json

def record_rework(root: Path, score: dict, query_text: str = '',
                  response_text: str = '') -> None:
    """Append a rework event to rework_log.json."""
    log_path = root / REWORK_STORE
    try:
        existing = json.loads(log_path.read_text('utf-8')) if log_path.exists() else []
    except Exception:
        existing = []
    entry = {
        'ts':           datetime.now(timezone.utc).isoformat(),
        'verdict':      score['verdict'],
        'rework_score': score['rework_score'],
        'del_ratio':    score['del_ratio'],
        'wpm':          score['wpm'],
        'query_hint':   query_text[:80],
    }
    if response_text:
        entry['response_hint'] = response_text[:200]
    existing.append(entry)
    # Keep last 200 events
    log_path.write_text(json.dumps(existing[-200:], indent=2), encoding='utf-8')
    # Feed rework verdict back into active bug dossier scores
    _update_dossier_scores(root, score['verdict'])


REWORK_STORE     = 'rework_log.json'


REWORK_WINDOW_MS = 30_000   # 30s after response = rework window
