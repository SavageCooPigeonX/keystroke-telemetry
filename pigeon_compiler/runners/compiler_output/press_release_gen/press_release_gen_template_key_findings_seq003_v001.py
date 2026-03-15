"""press_release_gen_template_key_findings_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 48 lines | ~564 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-03-15 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

def __generate_template_key_findings(mutations: list, news_corr: list) -> list:
    """Generate the key findings list."""
    key_findings = []
    sorted_mutations = sorted(mutations, key=lambda m: m.get('score', 0), reverse=True)
    for mut in sorted_mutations[:4]:
        field = mut.get('field', 'unknown').replace('_', ' ').title()
        mt = mut.get('mutation_type', 'UNKNOWN')
        score = mut.get('score', 0)

        if mt == 'REVERSAL':
            key_findings.append(
                f"**{field}**: AI models have REVERSED their assessment "
                f"(severity: {score:.1f}/10). Previously stated claims are now contradicted."
            )
        elif mt == 'ERASURE':
            key_findings.append(
                f"**{field}**: Information has DISAPPEARED from AI model responses "
                f"(severity: {score:.1f}/10). Previously cited data is no longer surfaced."
            )
        elif mt == 'FRAGMENTATION':
            key_findings.append(
                f"**{field}**: Model consensus has BROKEN (severity: {score:.1f}/10). "
                f"Models that previously agreed now give dramatically different responses."
            )
        elif mt == 'AMPLIFICATION':
            key_findings.append(
                f"**{field}**: Coverage has INTENSIFIED (severity: {score:.1f}/10). "
                f"AI models are providing significantly more detail than in prior audits."
            )
        elif mt == 'EVOLUTION':
            key_findings.append(
                f"**{field}**: Gradual shift detected (severity: {score:.1f}/10). "
                f"Narrative is evolving but maintaining general direction."
            )
        else:
            key_findings.append(f"**{field}**: {mt} detected (severity: {score:.1f}/10).")

    if news_corr:
        key_findings.append(
            f"**News Correlation**: {len(news_corr)} real-world event(s) correlate "
            f"with detected mutations. Top signal: \"{news_corr[0]['headline'][:80]}\"."
        )

    if not key_findings:
        key_findings.append("No significant mutations detected in this audit cycle.")
    return key_findings
