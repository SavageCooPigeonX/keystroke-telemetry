"""tc_profile_intelligence_time_seq013_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 013 | VER: v001 | 40 lines | ~497 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import Counter
import re
import time

def __deduce_intelligence_time_personality(sections, existing, now, model):
    from collections import Counter
    new_secrets = []
    key = 'time_personality'
    if key not in existing:
        all_hours = Counter()
        for sec in sections.values():
            if isinstance(sec, dict):
                for h, c in sec.get('hour_dist', {}).items():
                    all_hours[int(h)] += c
        if sum(all_hours.values()) >= 15:
            night = sum(all_hours.get(h, 0) for h in range(22, 24)) + sum(all_hours.get(h, 0) for h in range(0, 6))
            morning = sum(all_hours.get(h, 0) for h in range(6, 12))
            afternoon = sum(all_hours.get(h, 0) for h in range(12, 18))
            total = sum(all_hours.values())
            if night / total > 0.5:
                tp = 'night owl'
                desc = f'{night/total:.0%} of your activity is between 10pm-6am. your brain turns on when everyone else turns off.'
            elif morning / total > 0.5:
                tp = 'morning person'
                desc = f'{morning/total:.0%} morning activity. you front-load your cognitive budget.'
            elif night / total > 0.3 and afternoon / total > 0.3:
                tp = 'chaos schedule'
                desc = f'no pattern. {night/total:.0%} night, {afternoon/total:.0%} afternoon. you code when the mood hits.'
            else:
                tp = 'afternoon worker'
                desc = f'{afternoon/total:.0%} afternoon dominance. reliable schedule.'
            new_secrets.append({
                'key': key, 'type': 'temporal', 'discovered': now,
                'confidence': min(0.85, 0.4 + total * 0.01),
                'text': desc,
                'evidence': f'hour distribution across {total} data points',
            })
            model['time_personality'] = tp
    return new_secrets
