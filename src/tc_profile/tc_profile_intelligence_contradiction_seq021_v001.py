"""tc_profile_intelligence_contradiction_seq021_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 021 | VER: v001 | 37 lines | ~500 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def __deduce_intelligence_contradiction_detector(profile, sections, existing, now, intel):
    topics = profile['shards'].get('topics', {})
    recent_focus = topics.get('recent_focus', [])
    if recent_focus and sections:
        for sec_name, sec in sections.items():
            if not isinstance(sec, dict):
                continue
            stated = sec.get('stated_intents', [])
            actual = sec.get('actual_actions', [])
            if len(stated) >= 3 and len(actual) >= 3:
                stated_mods = set()
                for s in stated:
                    stated_mods.update(s.lower().split() if isinstance(s, str) else [])
                actual_mods = set()
                for a in actual:
                    if isinstance(a, list):
                        actual_mods.update(a)
                    elif isinstance(a, str):
                        actual_mods.update(a.split())
                talked_not_touched = stated_mods - actual_mods
                if len(talked_not_touched) > 2:
                    key_c = f'contradiction:{sec_name}'
                    if key_c not in existing:
                        intel['secrets'].append({
                            'key': key_c, 'type': 'contradiction', 'discovered': now,
                            'confidence': 0.6,
                            'text': f'in [{sec_name}] you talk about {", ".join(list(talked_not_touched)[:3])} '
                                    f'but never act on them. stated intent != actual behavior.',
                            'evidence': f'{len(stated)} stated, {len(actual)} actual in {sec_name}',
                        })
                        intel['contradictions'] = (intel.get('contradictions', []) + [{
                            'section': sec_name, 'stated': list(talked_not_touched)[:5],
                            'ts': now,
                        }])[-10:]
