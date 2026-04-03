"""Post-response rework detector — measures AI answer quality from typing signal.

After an AI response arrives, the next typing session is the ground truth:
heavy deletions + retype in <30s = answer didn't land. This module scores
the rework window and accumulates a per-session miss rate that feeds into
the coaching prompt so the AI learns its own failure patterns.

Zero LLM calls. Pure signal math.
"""
# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v006 | 185 lines | ~1,785 tokens
# DESC:   measures_ai_answer_quality_from
# INTENT: p0_p3_attribution
# LAST:   2026-04-03 @ d7cbc14
# SESSIONS: 1
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   2026-03-29T06:00:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  add composition-based scoring, fix dead formula
# EDIT_STATE: harvested
# ── /pulse ──
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

    # Rework score: high deletions early + slow typing = confused, rewriting
    speed_penalty = 0.15 * max(0, 1 - wpm / 40)  # 0.15 at 0 wpm, 0 at 40+ wpm
    rework_score = round(min(1.0, del_ratio * 0.7 + speed_penalty), 3)

    if rework_score > 0.55 or del_ratio > HEAVY_DEL_RATIO:
        verdict = 'miss'
    elif rework_score > 0.25:
        verdict = 'partial'
    else:
        verdict = 'ok'

    return {'rework_score': rework_score, 'del_ratio': round(del_ratio, 3),
            'wpm': wpm, 'verdict': verdict}


def score_rework_from_composition(composition: dict) -> dict:
    """Score rework from chat composition data (deleted words, rewrites).

    Composition data captures actual prompt-level deletions and rewrites —
    the high-fidelity path. When the operator deletes half their prompt and
    rewrites it, that's rework regardless of what the final text looks like.
    """
    del_ratio = composition.get('deletion_ratio', 0)
    rewrites = len(composition.get('rewrites', []))
    deleted_words = composition.get('deleted_words', [])
    duration_ms = max(composition.get('duration_ms', 1), 1)
    total_keys = max(composition.get('total_keystrokes', 1), 1)

    # Each rewrite adds 0.15 (capped at 0.45), deletion ratio adds up to 0.55
    rewrite_weight = min(rewrites * 0.15, 0.45)
    del_weight = del_ratio * 0.55
    rework_score = round(min(1.0, del_weight + rewrite_weight), 3)

    wpm = round((total_keys / 5) / max(duration_ms / 60_000, 0.001), 1)

    if rework_score > 0.45 or del_ratio > HEAVY_DEL_RATIO:
        verdict = 'miss'
    elif rework_score > 0.20 or rewrites >= 2:
        verdict = 'partial'
    else:
        verdict = 'ok'

    return {
        'rework_score': rework_score,
        'del_ratio': round(del_ratio, 3),
        'wpm': wpm,
        'verdict': verdict,
    }


def _update_dossier_scores(root: Path, verdict: str):
    """Feed rework verdict back into registry dossier_score for active bug entries."""
    dossier_path = root / 'logs' / 'active_dossier.json'
    if not dossier_path.exists(): return
    try:
        d = json.loads(dossier_path.read_text('utf-8'))
    except Exception: return
    focus = d.get('focus_modules', [])
    if not focus or d.get('confidence', 0) < 0.3: return
    reg_path = root / 'pigeon_registry.json'
    if not reg_path.exists(): return
    try:
        reg = json.loads(reg_path.read_text('utf-8'))
    except Exception: return
    files = reg if isinstance(reg, list) else reg.get('files', [])
    # Reward signal: ok → +0.05, partial → -0.02, miss → -0.1
    delta = {'ok': 0.05, 'partial': -0.02, 'miss': -0.1}.get(verdict, 0)
    if delta == 0: return
    changed = False
    for f in files:
        name = f.get('file', '') or f.get('desc', '')
        if name in focus:
            old = f.get('dossier_score', 0)
            f['dossier_score'] = round(max(-1.0, min(1.0, old + delta)), 3)
            changed = True
    if changed:
        try:
            reg_path.write_text(json.dumps(reg, indent=2, default=str), 'utf-8')
        except Exception: pass


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
