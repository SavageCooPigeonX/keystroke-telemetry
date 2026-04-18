"""tc_profile_seq001_v001_intelligence_behavioral_laws_seq022_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 022 | VER: v001 | 19 lines | ~241 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def __deduce_intelligence_behavioral_laws(sections, existing, intel):
    for sec_name, sec in sections.items():
        if not isinstance(sec, dict) or sec.get('visit_count', 0) < 8:
            continue
        sd = sec.get('state_dist', {})
        total_states = sum(sd.values())
        if total_states >= 8:
            for st, ct in sd.items():
                if ct / total_states > 0.7:
                    law = f'always_{st}_in_{sec_name}'
                    if law not in existing:
                        intel['behavioral_laws'] = (intel.get('behavioral_laws', []) + [{
                            'law': f'ALWAYS {st} when in [{sec_name}]',
                            'confidence': ct / total_states,
                            'evidence': f'{ct}/{total_states} visits',
                        }])[-15:]
                        existing.add(law)
