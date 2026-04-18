"""叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc_build_narrative_wrapper_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import os

def _build_narrative_prompt(
    intent: str,
    file_briefs: list[dict],
    rework_stats: dict | None,
    query_mem: dict | None,
    heat_map: dict | None,
    cross_context: dict | None = None,
    composition: dict | None = None,
) -> str:
    def _brief_line(b):
        seq = b['seq']
        ver = b['ver']
        tag = f'seq{seq:03d} v{ver:03d}' if isinstance(seq, int) else b['path']
        author = b.get('author', 'copilot')
        return (f'- **{b["name"]}** ({tag}, {b["tokens"]}tok, author={author}): '
                f'desc="{b["desc"]}", last_intent="{b["intent"]}", '
                f'{b["history_len"]} versions')

    files_block = '\n'.join(_brief_line(b) for b in file_briefs)

    signals = []
    if rework_stats:
        signals.append(f'Rework: miss_rate={rework_stats.get("miss_rate", 0)}, '
                       f'worst={rework_stats.get("worst_queries", [])}')
    if query_mem:
        gaps = query_mem.get('persistent_gaps', [])
        abandons = query_mem.get('recent_abandons', [])
        if gaps:
            signals.append(f'Recurring queries: {[g.get("query", "") for g in gaps[:3]]}')
        if abandons:
            signals.append(f'Recent abandons: {abandons[:3]}')
    if heat_map:
        complex_files = heat_map.get('complex_files', [])
        if complex_files:
            signals.append(f'High-hesitation files: {[c["module"] for c in complex_files[:3]]}')

    signals_block = '\n'.join(signals) if signals else 'No deep signals available yet.'

    # Cross-file dependency context
    cross_block = ''
    if cross_context:
        cross_lines = []
        for rel, ctx in cross_context.items():
            name = Path(rel).stem.split('_seq')[0]
            deps = ', '.join(Path(d).stem.split('_seq')[0] for d in ctx.get('imports_from', []))
            users = ', '.join(Path(u).stem.split('_seq')[0] for u in ctx.get('imported_by', []))
            parts = ([f'depends on [{deps}]'] if deps else []) + ([f'used by [{users}]'] if users else [])
            if parts: cross_lines.append(f'- {name}: {"; ".join(parts)}')
        if cross_lines: cross_block = '\n\nCROSS-FILE DEPS:\n' + '\n'.join(cross_lines)

    # Composition: what the operator deleted/rewrote while building this commit
    comp_block = ''
    if composition:
        dw = composition.get('deleted_words', [])
        dr = composition.get('deletion_ratio', 0)
        rw = composition.get('rewrites', 0)
        state = composition.get('chat_state', {}).get('state', '?')
        comp_parts = [f'cognitive_state={state}, deletion_ratio={dr}, rewrites={rw}']
        if dw:
            comp_parts.append(f'deleted_words={dw[:8]}')
        comp_block = '\n\nOPERATOR COMPOSITION (what they typed then deleted while writing this commit):\n' + ', '.join(comp_parts)

    return (
        f'You are writing a debugging-grade development narrative for a code push.\n'
        f'This codebase has THREE actors. Attribute every action to the correct one:\n'
        f'- **Operator**: the human who types prompts and gives directions\n'
        f'- **Copilot**: the AI that executes edits based on operator prompts\n'
        f'- **Pigeon**: the autonomous rename/split/compile engine that fires post-commit\n'
        f'NEVER say "the developer did X" when Copilot or Pigeon did X.\n\n'
        f'COMMIT INTENT: {intent}\n\n'
        f'FILES CHANGED:\n{files_block}\n\n'
        f'OPERATOR DEEP SIGNALS:\n{signals_block}{cross_block}{comp_block}\n\n'
        f'INSTRUCTIONS:\n'
        f'Write a development narrative (200-350 words) optimized for future debugging. '
        f'Each changed file "speaks" in first person — one paragraph each — '
        f'explaining: (1) why it was touched and BY WHOM (operator prompt, copilot edit, or pigeon rename), '
        f'(2) what assumption it makes that could break, '
        f'(3) one specific regression to watch for. '
        f'If cross-file dependencies exist, each file names what it gives/receives '
        f'and the exact failure mode if that contract changes. '
        f'If operator composition data shows deleted words or high deletion ratio, '
        f'note what the operator was struggling with — their hesitation IS signal. '
        f'End with: a 1-line "REGRESSION WATCHLIST" of the 3 most fragile points '
        f'in this push, and a 1-sentence summary of what this push accomplishes. '
        f'Use direct, technical prose. No markdown headers — just paragraphs.'
    )
