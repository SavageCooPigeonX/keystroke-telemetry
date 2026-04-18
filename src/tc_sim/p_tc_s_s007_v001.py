"""tc_sim_seq001_v001_historical_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v001 | 115 lines | ~1,089 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from src.tc_constants_seq001_v001_seq001_v001 import KEYSTROKE_LOG, DEFAULT_PAUSE_MS, ROOT
import json
import os
import re
import time

def _build_historical_context(pause: PausePoint) -> tuple[dict, dict]:
    """Reconstruct context AND trajectory from the pause point's time period.
    
    The current bug: replay uses LIVE context (today's conversation) when
    simulating a pause from days ago. This makes predictions meaningless.
    
    Fix: search chat_compositions for entries around this pause's timestamp.
    
    Returns: (context_dict, trajectory_dict)
    """
    from datetime import datetime, timezone
    import json
    
    compositions_path = ROOT / 'logs' / 'chat_compositions.jsonl'
    if not compositions_path.exists():
        return {}, {}
    
    # Convert pause timestamp (unix ms) to datetime
    pause_dt = datetime.fromtimestamp(pause.ts / 1000, tz=timezone.utc)
    
    # Load compositions from the same session (within 2 hours before pause)
    comps_before = []
    try:
        for line in compositions_path.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            ts_str = raw.get('ts', '')
            if not ts_str:
                continue
            try:
                entry_dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
            except Exception:
                continue
            # Keep entries within 2 hours BEFORE the pause
            delta = (pause_dt - entry_dt).total_seconds()
            if 0 < delta < 7200:  # 0-2 hours before
                cs = raw.get('chat_state', {})
                signals = cs.get('signals', {}) if isinstance(cs, dict) else {}
                comps_before.append({
                    'ts': ts_str,
                    'text': raw.get('final_text', '')[:500],
                    'state': cs.get('state', 'unknown') if isinstance(cs, dict) else 'unknown',
                    'wpm': signals.get('wpm', 0),
                    'del_ratio': raw.get('deletion_ratio', 0),
                    'deleted_words': [
                        d.get('word', '') if isinstance(d, dict) else str(d)
                        for d in raw.get('deleted_words', [])[-6:]
                    ],
                    'rewrites': [
                        f"{r.get('old', '')}→{r.get('new', '')}"[:80]
                        if isinstance(r, dict) else str(r)[:80]
                        for r in raw.get('rewrites', [])[-4:]
                    ],
                    'hesitations': len(raw.get('hesitation_windows', [])),
                    'duration_ms': raw.get('duration_ms', 0),
                })
    except Exception:
        return {}, {}
    
    # Take last 5 compositions before the pause
    comps_before = sorted(comps_before, key=lambda x: x['ts'])[-5:]
    
    if not comps_before:
        return {}, {}
    
    # Build context
    ctx = {
        'session_messages': [
            {'text': c['text'], 'intent': 'unknown'}
            for c in comps_before
        ],
        'session_info': {
            'intent': 'unknown',
            'cognitive_state': comps_before[-1].get('state', 'unknown'),
            'session_n': len(comps_before),
        },
    }
    
    # Build trajectory in the format expected by format_trajectory_for_prompt
    trajectory = {
        'turns': [
            {
                'prompt': c['text'],
                'state': c['state'],
                'wpm': c['wpm'],
                'del_ratio': c['del_ratio'],
                'deleted_words': c['deleted_words'],
                'rewrites': c['rewrites'],
                'hesitations': c['hesitations'],
                'duration_ms': c['duration_ms'],
                'response': '',  # no response capture for historical
            }
            for c in comps_before
        ],
        'phase': 'iterating',  # default
        'suppressed': [],
        'recent_states': [c['state'] for c in comps_before[-3:]],
    }
    
    # Collect all deleted words for suppressed intent
    all_deleted = []
    for c in comps_before:
        all_deleted.extend(c.get('deleted_words', []))
    trajectory['suppressed_intent'] = list(set(all_deleted))[-10:]
    
    return ctx, trajectory
