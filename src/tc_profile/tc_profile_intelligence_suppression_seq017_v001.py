"""tc_profile_intelligence_suppression_seq017_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 017 | VER: v001 | 26 lines | ~319 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import Counter
import re

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
