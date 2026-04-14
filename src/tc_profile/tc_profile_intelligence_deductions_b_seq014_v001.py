"""tc_profile_intelligence_deductions_b_seq014_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 014 | VER: v001 | 121 lines | ~1,553 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import Counter
import ast
import re

def __deduce_intelligence_frustration_response(sections, existing, now, model):
    new_secrets = []
    key = 'frustration_response'
    if key not in existing and len(sections) >= 2:
        frust_sections = [(name, sec) for name, sec in sections.items()
                          if isinstance(sec, dict)
                          and sec.get('state_dist', {}).get('frustrated', 0) >= 3]
        if frust_sections:
            for name, sec in frust_sections:
                trans = sec.get('state_transitions', {})
                frust_exits = {k: v for k, v in trans.items() if k.startswith('frustrated->')}
                if frust_exits:
                    most_common = max(frust_exits, key=frust_exits.get)
                    target = most_common.split('->')[1]
                    if target == 'focused':
                        response = 'pushes through'
                        desc = (f'when frustrated in [{name}], you push through to focused. '
                                f'{frust_exits[most_common]}x observed. you use frustration as fuel.')
                    elif target == 'abandoned':
                        response = 'abandons session'
                        desc = (f'when frustrated in [{name}], you abandon. '
                                f'{frust_exits[most_common]}x observed. you know when to walk away — or you give up too early.')
                    else:
                        response = 'switches context'
                        desc = (f'when frustrated in [{name}], you switch to [{target}]. '
                                f'{frust_exits[most_common]}x observed. you rotate instead of grinding.')
                    new_secrets.append({
                        'key': key, 'type': 'behavioral', 'discovered': now,
                        'confidence': min(0.85, 0.4 + frust_exits[most_common] * 0.1),
                        'text': desc,
                        'evidence': f'transition map in {name}: {frust_exits}',
                    })
                    model['frustration_response'] = response
                    break
    return new_secrets


def __deduce_intelligence_suppression_pattern(sections, existing, now):
    from collections import Counter
    new_secrets = []
    key = 'suppression_pattern'
    if key not in existing:
        all_suppressed = Counter()
        for sec in sections.values():
            if isinstance(sec, dict):
                for w, c in sec.get('suppressed_words', {}).items():
                    all_suppressed[w] += c
        top = all_suppressed.most_common(5)
        if top and top[0][1] >= 4:
            words_desc = ', '.join(f'"{w}" ({c}x)' for w, c in top[:3])
            new_secrets.append({
                'key': key, 'type': 'suppression', 'discovered': now,
                'confidence': min(0.9, 0.5 + top[0][1] * 0.05),
                'text': f'your most suppressed words: {words_desc}. you keep typing these '
                        f'and deleting them. they represent thoughts you want to express '
                        f'but keep censoring. the system sees every deletion.',
                'evidence': f'{sum(c for _, c in top)} total suppressions across {len(sections)} sections',
            })
    return new_secrets


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
