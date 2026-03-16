"""Recurring query detector + unsaid thought integrator.

Two signals:
  1. Recurring queries — same semantic question asked 3+ times across sessions
     = AI permanent failure surface on THIS operator's codebase.
  2. Unsaid integration — pipes unsaid_seq002 output into the persistent
     profile so abandoned drafts accumulate across sessions, not just per-message.

Both feed into the coaching prompt via load_query_memory().
Zero LLM calls.
"""
# ── pigeon ────────────────────────────────────
# SEQ: 010 | VER: v001 | src/
# DESC:   recurring_query_and_unsaid_integrator
# INTENT: build_deep_operator_profile
# ──────────────────────────────────────────────
from __future__ import annotations
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

QUERY_STORE  = 'query_memory.json'
MAX_ENTRIES  = 500
RECUR_THRESH = 3   # same fingerprint N times = persistent gap


def _fingerprint(text: str) -> str:
    """Stable semantic fingerprint: strip noise, keep core nouns/verbs."""
    text = text.lower().strip()
    # Remove common filler
    text = re.sub(r'\b(how|do|i|the|a|an|to|in|is|it|can|you|what|why|please|just|me|my|this)\b', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    words = sorted(set(text.split()))
    return ' '.join(words[:8])  # top 8 content words, sorted = order-invariant


def record_query(root: Path, query_text: str, submitted: bool,
                 unsaid: dict | None = None) -> None:
    """Persist a query + optional unsaid analysis to query_memory.json."""
    store_path = root / QUERY_STORE
    try:
        store = json.loads(store_path.read_text('utf-8')) if store_path.exists() else {}
    except Exception:
        store = {}

    queries  = store.get('queries', [])
    abandons = store.get('abandoned_themes', [])

    if submitted and query_text.strip():
        fp = _fingerprint(query_text)
        queries.append({
            'ts':          datetime.now(timezone.utc).isoformat(),
            'text':        query_text[:120],
            'fingerprint': fp,
            'submitted':   submitted,
        })

    # Integrate unsaid output
    if unsaid:
        for draft in unsaid.get('abandoned_drafts', []):
            if draft.get('text', '').strip():
                abandons.append({
                    'ts':    datetime.now(timezone.utc).isoformat(),
                    'text':  draft['text'][:120],
                    'state': draft.get('cognitive_state', 'unknown'),
                })
        for pivot in unsaid.get('topic_pivots', []):
            abandons.append({
                'ts':    datetime.now(timezone.utc).isoformat(),
                'text':  f"pivot: '{pivot.get('from_topic','?')}' → '{pivot.get('to_topic','?')}'",
                'state': 'pivot',
            })

    store['queries']           = queries[-MAX_ENTRIES:]
    store['abandoned_themes']  = abandons[-MAX_ENTRIES:]
    store_path.write_text(json.dumps(store, indent=2), encoding='utf-8')


def load_query_memory(root: Path) -> dict:
    """Load and aggregate query memory → summary for coaching prompt."""
    store_path = root / QUERY_STORE
    if not store_path.exists():
        return {}
    try:
        store = json.loads(store_path.read_text('utf-8'))
    except Exception:
        return {}

    queries  = store.get('queries', [])
    abandons = store.get('abandoned_themes', [])

    # Find recurring fingerprints
    fps = [q['fingerprint'] for q in queries if q.get('fingerprint')]
    counts = Counter(fps)
    persistent_gaps = [
        {'query': next((q['text'] for q in queries if q['fingerprint'] == fp), fp),
         'count': cnt}
        for fp, cnt in counts.most_common(5)
        if cnt >= RECUR_THRESH
    ]

    # Recent abandoned themes (last 10)
    recent_abandons = [a['text'] for a in abandons[-10:]]

    # Unsaid emotion distribution
    emotion_pattern = re.compile(r"pivot:|→")
    pivots = [a for a in abandons if emotion_pattern.search(a.get('text', ''))]

    return {
        'total_queries':     len(queries),
        'unique_topics':     len(counts),
        'persistent_gaps':   persistent_gaps,   # recurring = AI kept failing here
        'recent_abandons':   recent_abandons,    # what they started but didn't send
        'topic_pivot_count': len(pivots),
    }
