"""推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 32 lines | ~367 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json, re, subprocess

_GENERIC_UNSAID_PREFIXES = (
    'the user was',
    'the operator was',
    'it seems the user was',
    'it seems the operator was',
    'perhaps the user was',
    'perhaps the operator was',
)


_COT = {
    'frustrated': 'Operator is frustrated. Think step-by-step but keep output SHORT. Lead with the fix. Skip explanations unless asked. If unsure, say so in one line then give your best option.',
    'hesitant':   'Operator is uncertain. Think through what they MIGHT mean. Offer 2 interpretations and address both. End with a clarifying question.',
    'flow':       'Operator is in flow. Match their speed \u2014 technical depth, no preamble. Assume expertise. Go deeper than they asked.',
    'restructuring': 'Operator is rewriting/restructuring. Be precise. Use numbered steps and headers. Match the effort they put into their prompt.',
    'abandoned':  'Operator previously abandoned a message. They may be re-approaching. Be direct and welcoming.',
}


_MEASURED_INPUTS = frozenset({
    'wpm', 'deletion_ratio', 'hesitation_count', 'chars_per_sec',
    'rewrite_count', 'total_keystrokes', 'duration_ms',
    'typo_corrections', 'intentional_deletions',
})

_DERIVED_INPUTS = frozenset({
    'coaching', 'unsaid', 'narrative_risks', 'self_fix_crit',
    'trajectory', 'gaps', 'file_consciousness', 'codebase_health',
})
