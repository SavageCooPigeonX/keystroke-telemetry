"""git_plugin_coaching_prompt_seq014_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 014 | VER: v001 | 126 lines | ~1,333 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import ast
import os
import re
import sys

def _build_commit_coaching_prompt(
    intent: str,
    renames: list,
    box_only: list,
    registry: dict,
    history: list,
    rework_stats: dict | None = None,
    query_mem: dict | None = None,
    heat_map: dict | None = None,
) -> str:
    """Build the DeepSeek prompt combining commit context + all deep operator signals."""
    from collections import Counter

    # Changed files summary
    file_lines = []
    for old_rel, new_rel, entry, tokens, _ in renames:
        ver = entry.get('ver', 1)
        file_lines.append(f'  RENAMED  v{ver} {tokens}tok  {Path(old_rel).name} → {Path(new_rel).name}')
    for abs_p, entry, old_rel, tokens, _ in box_only:
        ver = entry.get('ver', 1)
        file_lines.append(f'  UPDATED  v{ver} {tokens}tok  {Path(old_rel).name}')
    files_block = '\n'.join(file_lines) or '  (none parsed)'

    # Registry churn — top pain-point modules
    churn = _registry_churn(registry)
    churn_lines = '\n'.join(
        f'  {c["module"]} seq{c["seq"]} v{c["ver"]}  {c["tokens"]}tok  [{c["desc"]}] last: {c["intent"]}'
        for c in churn
    )

    # Operator profile summary
    n = len(history)
    submitted = sum(1 for h in history if h.get('submitted', True))
    states = [h.get('state', 'neutral') for h in history]
    state_dist = dict(Counter(states).most_common())
    wpms = [h['wpm'] for h in history if 'wpm' in h]
    hess = [h['hesitation'] for h in history if 'hesitation' in h]
    dels = [h['del_ratio'] for h in history if 'del_ratio' in h]
    slots = [h.get('slot', '') for h in history if h.get('slot')]
    avg_wpm = round(sum(wpms) / len(wpms), 1) if wpms else 0
    avg_hes = round(sum(hess) / len(hess), 3) if hess else 0
    avg_del = round(sum(dels) / len(dels) * 100, 1) if dels else 0
    slot_dist = dict(Counter(slots).most_common(3))
    recent = history[-8:]
    recent_block = '\n'.join(
        f'  msg{i+1}: {h.get("state","?")} wpm={h.get("wpm",0)} '
        f'del={round(h.get("del_ratio",0)*100)}% hes={h.get("hesitation",0)} '
        f'sub={h.get("submitted",True)} slot={h.get("slot","?")}'
        for i, h in enumerate(recent)
    )

    # Deep signal blocks (optional — populated after a few sessions)
    rework_block = ''
    if rework_stats:
        worst = rework_stats.get('worst_queries', [])
        rework_block = (
            f'\nAI RESPONSE QUALITY (post-response rework rate):\n'
            f'  miss_rate={rework_stats.get("miss_rate","?")}  '
            f'({rework_stats.get("miss_count","?")} misses / '
            f'{rework_stats.get("total_responses","?")} responses)\n'
            f'  worst queries: {worst[:3]}'
        )

    gaps_block = ''
    if query_mem and query_mem.get('persistent_gaps'):
        gaps = '\n'.join(
            f'  [{g["count"]}x] {g["query"]}'
            for g in query_mem['persistent_gaps']
        )
        abandon_lines = '\n'.join(
            f'  {a}' for a in query_mem.get('recent_abandons', [])[:3]
        ) or '  none'
        gaps_block = (
            f'\nPERSISTENT GAPS (operator keeps asking same thing → AI keeps failing):\n'
            f'{gaps}\n'
            f'ABANDONED/UNSAID recent:\n{abandon_lines}'
        )

    heat_block = ''
    if heat_map and heat_map.get('complex_files'):
        cf = '\n'.join(
            f'  {c["module"]} avg_hes={c["avg_hes"]} avg_wpm={c["avg_wpm"]} '
            f'misses={c["miss_count"]}/{c["samples"]}'
            for c in heat_map['complex_files'][:5]
        )
        mf = '\n'.join(
            f'  {m["module"]} miss_rate={m["miss_rate"]}'
            for m in heat_map.get('high_miss_files', [])[:3]
        ) or '  none'
        heat_block = (
            f'\nFILE COMPLEXITY DEBT (high hesitation when working on these):\n{cf}\n'
            f'HIGH AI-MISS FILES:\n{mf}'
        )

    return f"""You are a behavioral AI coach embedded in a VS Code extension.
Your output is injected DIRECTLY into a Copilot system prompt — write INSTRUCTIONS for the AI, not a report.

THIS COMMIT (intent: {intent}):
{files_block}

REGISTRY CHURN — most-mutated modules (recurring pain points the operator keeps revisiting):
{churn_lines}

OPERATOR TYPING HISTORY ({n} total messages, {submitted} submitted):
  state distribution: {state_dist}
  avg WPM: {avg_wpm} | avg hesitation: {avg_hes} | avg deletion rate: {avg_del}%
  active time slots: {slot_dist}
  recent 8 messages:
{recent_block}{rework_block}{gaps_block}{heat_block}

Write behavioral coaching instructions for Copilot. Requirements:
1. One sentence: what this operator just built + what their typing patterns reveal about HOW they work
2. 4-6 concrete bullets: exactly how Copilot should respond in the next session
3. Name specific modules from the churn list that keep getting touched — what should Copilot anticipate?
4. If rework/gap data present: prescribe explicit strategies for the failing areas
5. If typing shows frustration/hesitation on heavy-edit commits → call that out and prescribe a response
6. One sentence: what this operator is most likely building toward next

Be surgical and specific. Every word must change AI behavior. No generic advice. Max 250 words. Plain markdown bullets only."""
