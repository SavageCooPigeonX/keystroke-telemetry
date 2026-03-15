"""press_release_gen_template_helpers_seq004_v001_seq001_v001.py — Pigeon-extracted by compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 43 lines | ~600 tokens
# DESC:   pigeon_extracted_by_compiler
# INTENT: (none)
# LAST:   2026-03-15 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def __generate_template_exec_summary(entity_name: str, severity: float, risk_level: str,
                                     mut_count: int, c_count: int) -> str:
    """Generate the executive summary."""
    if risk_level in ('CRITICAL', 'HIGH'):
        exec_summary = (
            f"MyAIFingerprint's Drift Intelligence engine has detected {mut_count} "
            f"persona mutations for {entity_name} across the last two audit cycles. "
            f"Of these, {c_count} represent direct contradictions — instances where "
            f"AI models have reversed or erased prior assessments. "
            f"The composite severity score of {severity:.1f}/10 places this entity "
            f"in the {risk_level} risk category, triggering accelerated monitoring."
        )
    elif mut_count > 0:
        contradiction_text = f"These include {c_count} contradiction(s) where new data reverses prior findings. " if c_count else ''
        exec_summary = (
            f"Routine drift monitoring for {entity_name} has identified {mut_count} "
            f"mutations in how AI models describe this entity. "
            f"{contradiction_text}"
            f"Severity: {severity:.1f}/10 ({risk_level})."
        )
    else:
        exec_summary = (
            f"{entity_name}'s AI reputation profile remains consistent across all 7 models. "
            f"No significant mutations detected in this audit cycle. "
            f"Continued monitoring scheduled."
        )
    return exec_summary
def __generate_template_headline(entity_name: str, risk_level: str, mut_count: int, c_count: int) -> str:
    """Generate the headline."""
    if risk_level == 'CRITICAL':
        headline = (f"CRITICAL: AI Models Show Major Perception Shift for {entity_name} — "
                    f"{c_count} Contradictions Flagged Across 7 Models")
    elif risk_level == 'HIGH':
        headline = (f"ALERT: {entity_name}'s AI Reputation Shows Significant Changes — "
                    f"{mut_count} Mutations Detected")
    elif c_count > 0:
        headline = (f"UPDATE: AI Models Disagree on {entity_name} — "
                    f"{c_count} Contradiction(s) Flagged in Latest Audit")
    else:
        headline = f"STATUS: {entity_name}'s Digital Presence Holds Steady Across AI Models"
    return headline
