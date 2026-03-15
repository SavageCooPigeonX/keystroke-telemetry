"""press_release_gen_template_builders_seq002_v001_seq003_v001.py — Pigeon-extracted by compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 20 lines | ~235 tokens
# DESC:   pigeon_extracted_by_compiler
# INTENT: (none)
# LAST:   2026-03-15 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def __generate_template_social_and_stat(entity_name: str, severity: float,
                                        mut_count: int, c_count: int) -> tuple:
    """Generate the social headline and key stat."""
    if c_count > 0:
        social = f"⚡ {c_count} contradictions found in how AI sees {entity_name}"
    elif mut_count > 0:
        social = f"📊 {mut_count} changes detected in {entity_name}'s AI profile"
    else:
        social = f"✅ {entity_name}'s AI reputation holds steady"

    if c_count > 0:
        key_stat = f"{c_count} direct contradictions across 7 AI models in {mut_count} total mutations"
    elif mut_count > 0:
        key_stat = f"{mut_count} mutations detected | Severity: {severity:.1f}/10"
    else:
        key_stat = "0 mutations detected — profile stable across all 7 models"

    return social, key_stat
