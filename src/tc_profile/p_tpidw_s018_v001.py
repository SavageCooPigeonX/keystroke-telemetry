"""tc_profile_seq001_v001_intelligence_decision_work_seq018_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 018 | VER: v001 | 59 lines | ~732 tokens
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


def __deduce_intelligence_work_style(sections, existing, now, model):
    new_secrets = []
    key = 'work_style'
    if key not in existing and len(sections) >= 2:
        visits_per_section = [sec.get('visit_count', 0) for sec in sections.values() if isinstance(sec, dict)]
        if visits_per_section:
            max_v = max(visits_per_section)
            spread = len([v for v in visits_per_section if v > max_v * 0.3])
            total_v = sum(visits_per_section)
            if max_v / max(total_v, 1) > 0.7:
                ws = 'deep diver'
                desc = f'{max_v/total_v:.0%} of visits in one section. you tunnel in and stay.'
            elif spread >= 4:
                ws = 'butterfly'
                desc = f'{spread} sections with significant activity. you context-switch constantly.'
            else:
                ws = 'circuit runner'
                desc = f'you rotate through {spread} sections in cycles. predictable orbit.'
            new_secrets.append({
                'key': key, 'type': 'personality', 'discovered': now,
                'confidence': min(0.8, 0.4 + total_v * 0.01),
                'text': desc, 'evidence': f'{total_v} total visits across {len(visits_per_section)} sections',
            })
            model['work_style'] = ws
    return new_secrets
