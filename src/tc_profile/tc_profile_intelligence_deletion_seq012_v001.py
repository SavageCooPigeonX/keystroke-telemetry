"""tc_profile_intelligence_deletion_seq012_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 012 | VER: v001 | 43 lines | ~593 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

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
