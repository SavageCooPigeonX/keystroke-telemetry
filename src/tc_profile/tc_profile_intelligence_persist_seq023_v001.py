"""tc_profile_intelligence_persist_seq023_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 023 | VER: v001 | 13 lines | ~149 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import ast
import re

def __deduce_intelligence_persist(new_secrets, sections, intel, model, now):
    if new_secrets:
        intel['secrets'] = intel.get('secrets', []) + new_secrets
        intel['secret_count'] = len(intel['secrets'])
        intel['last_deduction'] = now
        contradictions = len(intel.get('contradictions', []))
        total_sections = len(sections)
        if total_sections > 0:
            model['honesty_index'] = round(1.0 - (contradictions / max(total_sections * 3, 1)), 2)
