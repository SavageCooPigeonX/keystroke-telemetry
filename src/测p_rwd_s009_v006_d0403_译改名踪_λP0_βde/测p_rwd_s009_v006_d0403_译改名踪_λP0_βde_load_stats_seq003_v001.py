"""测p_rwd_s009_v006_d0403_译改名踪_λP0_βde_load_stats_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 33 lines | ~303 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def load_rework_stats(root: Path) -> dict:
    """Aggregate rework_log.json → summary stats for coaching prompt."""
    log_path = root / REWORK_STORE
    if not log_path.exists():
        return {}
    try:
        events = json.loads(log_path.read_text('utf-8'))
    except Exception:
        return {}
    if not events:
        return {}
    total   = len(events)
    misses  = sum(1 for e in events if e['verdict'] == 'miss')
    partials = sum(1 for e in events if e['verdict'] == 'partial')
    miss_rate = round(misses / total, 3)
    scores   = [e['rework_score'] for e in events]
    avg_score = round(sum(scores) / len(scores), 3)
    # Worst queries (highest rework)
    worst = sorted(events, key=lambda e: e['rework_score'], reverse=True)[:3]
    return {
        'total_responses':   total,
        'miss_count':        misses,
        'partial_count':     partials,
        'miss_rate':         miss_rate,
        'avg_rework_score':  avg_score,
        'worst_queries':     [w['query_hint'] for w in worst],
    }

REWORK_STORE     = 'rework_log.json'
