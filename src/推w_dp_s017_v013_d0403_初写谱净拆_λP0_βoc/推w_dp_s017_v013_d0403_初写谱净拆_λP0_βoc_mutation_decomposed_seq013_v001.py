"""推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_mutation_decomposed_seq013_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 013 | VER: v001 | 52 lines | ~579 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json, re, subprocess

def _mutation_effectiveness(root):
    """Read mutation_scores.json and summarize which prompt sections help/hurt."""
    ms = _json(root / 'logs' / 'mutation_scores.json')
    if not ms or ms.get('total_pairs', 0) < 5:
        return None
    sections = ms.get('sections', {})
    if not sections:
        return None
    # Find sections with measurable signal
    helpful = []
    harmful = []
    neutral = []
    for name, stats in sections.items():
        w = stats.get('with_section')
        wo = stats.get('without_section')
        n = stats.get('n_with', 0)
        if n < 3:
            continue
        short = name[:50]
        if w is not None and wo is not None:
            delta = w - wo
            if delta > 0.05:
                helpful.append((short, w, delta, n))
            elif delta < -0.05:
                harmful.append((short, w, delta, n))
            else:
                neutral.append((short, w, n))
        elif w is not None:
            neutral.append((short, w, n))
    lines = [f'### Mutation Effectiveness *[source: measured]*',
             f'*{ms.get("total_pairs", 0)} rework pairs \u00d7 {ms.get("total_mutations", 0)} mutations scored*']
    if helpful:
        lines.append('**Helpful sections** (presence → better AI answers):')
        for name, rate, delta, n in sorted(helpful, key=lambda x: -x[2])[:5]:
            lines.append(f'- `{name}` hit={rate:.0%} (+{delta:.0%}, n={n})')
    if harmful:
        lines.append('**Harmful sections** (presence → worse AI answers):')
        for name, rate, delta, n in sorted(harmful, key=lambda x: x[2])[:5]:
            lines.append(f'- `{name}` hit={rate:.0%} ({delta:.0%}, n={n})')
    if not helpful and not harmful:
        lines.append(f'*No significant signal yet — all {len(neutral)} sections scored neutral.*')
    # Patch application stats
    pa = _json(root / 'logs' / 'cognitive_reactor_state.json')
    if pa:
        fires = pa.get('total_fires', 0)
        applied = pa.get('patches_applied', 0)
        if fires > 0:
            lines.append(f'\n**Reactor patches:** {applied}/{fires} applied ({round(applied/fires*100)}% acceptance)')
    return '\n'.join(lines)
