"""tc_profile_format_intelligence_decomposed_seq025_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 025 | VER: v001 | 62 lines | ~742 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re
import time

_current_section = 'unknown'

def format_intelligence_for_prompt(profile: dict) -> str:
    """Format the intelligence file for injection into the thought completer prompt.

    The goal: the completion should casually reference something the operator
    didn't know the system knew. Scary-accurate behavioral predictions.
    """
    intel = profile.get('shards', {}).get('intelligence', {})
    secrets = intel.get('secrets', [])
    model_d = intel.get('operator_model', {})
    laws = intel.get('behavioral_laws', [])
    sections = profile.get('shards', {}).get('sections', {})

    if not secrets and not model_d:
        return ''

    lines = ['OPERATOR INTELLIGENCE FILE (discovered from behavioral signals):']

    # model summary
    traits = []
    if model_d.get('deletion_personality'):
        traits.append(f'deletion={model_d["deletion_personality"]}')
    if model_d.get('decision_speed'):
        traits.append(f'decisions={model_d["decision_speed"]}')
    if model_d.get('work_style'):
        traits.append(f'work={model_d["work_style"]}')
    if model_d.get('time_personality'):
        traits.append(f'schedule={model_d["time_personality"]}')
    if model_d.get('frustration_response'):
        traits.append(f'frustration={model_d["frustration_response"]}')
    if traits:
        lines.append(f'OPERATOR MODEL: {" | ".join(traits)}')

    # top secrets by confidence
    top = sorted(secrets, key=lambda s: s.get('confidence', 0), reverse=True)[:5]
    for s in top:
        lines.append(f'SECRET [{s.get("type", "?")}] (conf={s.get("confidence", 0):.0%}): {s.get("text", "")}')

    # behavioral laws
    for law in laws[-3:]:
        lines.append(f'LAW: {law.get("law", "")} (conf={law.get("confidence", 0):.0%})')

    # current section dossier
    if _current_section and _current_section in sections:
        sec = sections[_current_section]
        if isinstance(sec, dict) and sec.get('visit_count', 0) >= 3:
            lines.append(f'CURRENT SECTION: {_current_section} (visited {sec["visit_count"]}x)')
            if sec.get('suppressed_words'):
                top_supp = sorted(sec['suppressed_words'].items(), key=lambda x: x[1], reverse=True)[:3]
                lines.append(f'  SUPPRESSED HERE: {", ".join(f"{w}({c}x)" for w, c in top_supp)}')
            if sec.get('dominant_state') != 'unknown':
                lines.append(f'  USUAL STATE HERE: {sec["dominant_state"]}')
            if sec.get('avg_accepted_len') and sec.get('avg_rejected_len'):
                lines.append(f'  STYLE THAT WORKS: ~{sec["avg_accepted_len"]:.0f} chars '
                             f'(rejected avg: {sec["avg_rejected_len"]:.0f})')

    lines.append('USE these signals to predict what they will type. Reference behavioral '
                 'patterns naturally — as if YOU noticed them, not as if reading a file.')
    return '\n'.join(lines)
