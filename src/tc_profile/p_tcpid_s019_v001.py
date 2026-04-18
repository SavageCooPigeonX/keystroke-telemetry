"""tc_profile_seq001_v001_intelligence_decision_seq019_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 019 | VER: v001 | 32 lines | ~401 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import ast
import re

def __deduce_intelligence_decision_speed(profile, existing, now, model):
    new_secrets = []
    rhythm = profile['shards'].get('rhythm', {})
    avg_del = rhythm.get('avg_del_ratio', 0)
    decisions = profile['shards'].get('decisions', {})
    key = 'decision_speed'
    if key not in existing and profile.get('samples', 0) >= 15:
        avg_wpm = rhythm.get('avg_wpm', 0)
        accept_rate = decisions.get('accept_rate', 0)
        if avg_wpm > 60 and avg_del < 0.15:
            speed = 'impulsive'
            desc = f'WPM={avg_wpm:.0f}, deletion={avg_del:.0%}. you type fast and rarely revise. first instinct, shipped.'
        elif avg_wpm < 30 and avg_del > 0.3:
            speed = 'paralyzed'
            desc = f'WPM={avg_wpm:.0f}, deletion={avg_del:.0%}. slow typing, heavy editing. every word is a negotiation.'
        elif avg_wpm > 40 and avg_del > 0.25:
            speed = 'iterative'
            desc = f'WPM={avg_wpm:.0f}, deletion={avg_del:.0%}. fast but revisionary. think-out-loud style.'
        else:
            speed = 'deliberate'
            desc = f'WPM={avg_wpm:.0f}, deletion={avg_del:.0%}. measured. you compose before committing.'
        new_secrets.append({
            'key': key, 'type': 'personality', 'discovered': now,
            'confidence': min(0.85, 0.5 + profile.get('samples', 0) * 0.005),
            'text': desc, 'evidence': f'{profile.get("samples", 0)} samples',
        })
        model['decision_speed'] = speed
    return new_secrets
