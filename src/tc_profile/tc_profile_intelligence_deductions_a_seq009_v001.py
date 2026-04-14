"""tc_profile_intelligence_deductions_a_seq009_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 009 | VER: v001 | 109 lines | ~1,428 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import Counter
import re
import time

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


def __deduce_intelligence_deletion_personality(profile, existing, now, model):
    new_secrets = []
    rhythm = profile['shards'].get('rhythm', {})
    avg_del = rhythm.get('avg_del_ratio', 0)
    sections = profile['shards'].get('sections', {})
    key = 'deletion_personality'
    if key not in existing and profile.get('samples', 0) >= 20:
        if avg_del > 0.35:
            abandon_total = sum(sec.get('abandon_count', 0)
                                for sec in sections.values() if isinstance(sec, dict))
            total_visits = sum(sec.get('visit_count', 0)
                               for sec in sections.values() if isinstance(sec, dict))
            abandon_rate = abandon_total / max(total_visits, 1)
            if abandon_rate > 0.3:
                personality = 'abandoner'
                desc = (f'you delete {avg_del:.0%} of what you type and abandon '
                        f'{abandon_rate:.0%} of attempts. you start thoughts you '
                        f"can't commit to. the system sees {abandon_total} abandoned "
                        f'messages across {total_visits} visits.')
            else:
                personality = 'editor'
                desc = (f'you delete {avg_del:.0%} of what you type but rarely abandon. '
                        f'you refine through destruction — the first draft is never the '
                        f'message. your real thought emerges from what survives the cuts.')
        elif avg_del < 0.1:
            personality = 'committer'
            desc = (f'you delete only {avg_del:.0%} of what you type. first thought = final '
                    f'thought. you trust your instincts and ship. this means your deletions '
                    f'carry HEAVY signal — when you DO delete, it matters.')
        else:
            personality = 'balanced'
            desc = f'deletion ratio {avg_del:.0%} — standard range.'
        new_secrets.append({
            'key': key, 'type': 'personality', 'discovered': now,
            'confidence': min(0.9, 0.5 + profile.get('samples', 0) * 0.005),
            'text': desc,
            'evidence': f'{profile.get("samples", 0)} samples, avg_del={avg_del:.3f}',
        })
        model['deletion_personality'] = personality
    return new_secrets


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
