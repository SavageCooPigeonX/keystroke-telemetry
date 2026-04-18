"""tc_profile_seq001_v001_intelligence_frustration_suppression_seq015_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 015 | VER: v001 | 63 lines | ~850 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import Counter
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
