"""tc_profile_seq001_v001_intelligence_comfort_seq010_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 010 | VER: v001 | 28 lines | ~384 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def __deduce_intelligence_comfort_avoidance(sections, existing, now, model):
    new_secrets = []
    if len(sections) >= 3:
        by_accept = [(name, sec.get('accepted', 0) / max(sec.get('total_completions', 1), 1),
                       sec.get('avg_hesitation', 0), sec.get('visit_count', 0))
                      for name, sec in sections.items()
                      if isinstance(sec, dict) and sec.get('visit_count', 0) >= 5]
        if by_accept:
            by_accept.sort(key=lambda x: x[1], reverse=True)
            best = by_accept[0]
            worst = by_accept[-1]
            if best[0] != worst[0]:
                key = f'comfort:{best[0]}'
                if key not in existing:
                    new_secrets.append({
                        'key': key, 'type': 'comfort_zone', 'discovered': now,
                        'confidence': min(0.95, 0.5 + best[3] * 0.02),
                        'text': f'you are most yourself in [{best[0]}] — accept rate {best[1]:.0%}, '
                                f'hesitation {best[2]:.2f}. you struggle in [{worst[0]}] — '
                                f'accept rate {worst[1]:.0%}, hesitation {worst[2]:.2f}.',
                        'evidence': f'{best[3]} visits to {best[0]}, {worst[3]} to {worst[0]}',
                    })
                    model['comfort_zones'] = [best[0]]
                    model['avoidance_zones'] = [worst[0]]
    return new_secrets
