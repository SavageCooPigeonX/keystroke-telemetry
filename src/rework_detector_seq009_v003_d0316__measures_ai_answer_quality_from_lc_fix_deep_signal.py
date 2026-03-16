"""Post-response rework detector — measures AI answer quality from typing signal.

After an AI response arrives, the next typing session is the ground truth:
heavy deletions + retype in <30s = answer didn't land. This module scores
the rework window and accumulates a per-session miss rate that feeds into
the coaching prompt so the AI learns its own failure patterns.

Zero LLM calls. Pure signal math.
"""
# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v003 | 106 lines | ~1,024 tokens
# DESC:   measures_ai_answer_quality_from
# INTENT: fix_deep_signal
# LAST:   2026-03-16 @ 1c7d33d
# SESSIONS: 2
# ──────────────────────────────────────────────
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

REWORK_WINDOW_MS = 30_000   # 30s after response = rework window
HEAVY_DEL_RATIO  = 0.35     # deletion rate threshold for "rework"
REWORK_STORE     = 'rework_log.json'


def score_rework(post_events: list) -> dict:
    """Score keystroke events from the post-response window.

    Returns:
        {rework_score: 0–1, del_ratio, wpm, verdict: 'miss'|'partial'|'ok'}
    """
    if not post_events:
        return {'rework_score': 0.0, 'del_ratio': 0.0, 'wpm': 0.0, 'verdict': 'ok'}

    inserts  = [e for e in post_events if e.get('type') == 'insert']
    deletes  = [e for e in post_events if e.get('type') == 'backspace']
    # del_ratio = deletes / (inserts + deletes) only — exclude pauses from denominator
    # so that a pause-heavy but delete-heavy window still scores as rework
    keystroke_total = max(len(inserts) + len(deletes), 1)
    del_ratio = len(deletes) / keystroke_total

    ts_vals  = [e['ts'] for e in post_events if 'ts' in e]
    dur_ms   = max((max(ts_vals) - min(ts_vals)) if len(ts_vals) > 1 else 1.0, 1.0)
    wpm      = round((len(inserts) / 5) / max(dur_ms / 60_000, 0.001), 1)

    # Rework score: high deletions early + low WPM = confused, rewriting
    rework_score = round(min(1.0, del_ratio * 0.7 + (1 / max(wpm, 1)) * 0.003), 3)

    if rework_score > 0.55 or del_ratio > HEAVY_DEL_RATIO:
        verdict = 'miss'
    elif rework_score > 0.25:
        verdict = 'partial'
    else:
        verdict = 'ok'

    return {'rework_score': rework_score, 'del_ratio': round(del_ratio, 3),
            'wpm': wpm, 'verdict': verdict}


def record_rework(root: Path, score: dict, query_text: str = '') -> None:
    """Append a rework event to rework_log.json."""
    log_path = root / REWORK_STORE
    try:
        existing = json.loads(log_path.read_text('utf-8')) if log_path.exists() else []
    except Exception:
        existing = []
    existing.append({
        'ts':           datetime.now(timezone.utc).isoformat(),
        'verdict':      score['verdict'],
        'rework_score': score['rework_score'],
        'del_ratio':    score['del_ratio'],
        'wpm':          score['wpm'],
        'query_hint':   query_text[:80],
    })
    # Keep last 200 events
    log_path.write_text(json.dumps(existing[-200:], indent=2), encoding='utf-8')


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
