"""tc_sim_diagnose_seq025_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 025 | VER: v001 | 51 lines | ~501 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import os
import re

def diagnose_from_results(results: list[SimResult]) -> list[dict]:
    """Analyze sim results to identify patchable bugs."""
    bugs = []

    # Bug: context agent always selects same files
    ctx_counts: dict[str, int] = {}
    for r in results:
        for f in r.context_files:
            ctx_counts[f] = ctx_counts.get(f, 0) + 1
    total = len(results) or 1
    for f, count in ctx_counts.items():
        if count > total * 0.5:
            bugs.append({
                'id': f'static_context_{f.split("_seq")[0]}',
                'severity': 'high',
                'file': 'src/tc_context_agent.py',
                'desc': f'context agent selected "{f}" in {count}/{total} '
                        f'({count/total:.0%}) predictions — not adapting to buffer',
                'fix': 'deduplicate_registry_results',
            })

    # Bug: duplicate context files in single prediction
    dup_count = sum(1 for r in results
                    if len(r.context_files) != len(set(r.context_files)))
    if dup_count > 0:
        bugs.append({
            'id': 'duplicate_context',
            'severity': 'high',
            'file': 'src/tc_context_agent.py',
            'desc': f'{dup_count}/{total} predictions had duplicate context files '
                    f'— registry has multiple entries with same stem name',
            'fix': 'deduplicate_registry_results',
        })

    # Bug: zero overlap predictions (context completely wrong)
    zero_count = sum(1 for r in results if r.word_overlap == 0)
    if zero_count > total * 0.3:
        bugs.append({
            'id': 'zero_overlap',
            'severity': 'medium',
            'file': 'src/tc_context_agent.py',
            'desc': f'{zero_count}/{total} predictions had 0% word overlap '
                    f'— stopwords may be filtering meaningful words',
            'fix': 'reduce_stopwords',
        })

    return bugs
