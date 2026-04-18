"""u_pe_s024_v004_d0403_λP0_βoc_prompt_builder_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
import os
import re

def _build_deepseek_prompt(raw_query: str, context: dict) -> str:
    hot = context.get('hot_files', [])
    rework = context.get('rework_history', [])
    past = context.get('past_attempts', [])
    deleted = context.get('deleted_words', [])
    state = context.get('cognitive_state', {})
    registry = context.get('registry_hits', [])
    journal = context.get('journal_trajectory', [])
    shard_context = context.get('shard_context', '')
    bug_dossier = context.get('bug_dossier', '')

    hot_str = '\n'.join(
        f"  • {h['file']} (hes={h['hes']}, touched {h['touches']}x)" for h in hot
    ) or '  (none)'

    rework_str = '\n'.join(
        f"  • [{e.get('verdict','?')}] \"{e.get('query_hint','')[:80]}\"" for e in rework
    ) or '  (no rework history for this topic)'

    past_str = '\n'.join(
        f"  • Prompt: \"{h['prompt_preview']}\"\n    Copilot: \"{h['response_preview']}\"" for h in past
    ) or '  (no past attempts found)'

    deleted_str = ', '.join(f'"{w}"' for w in deleted) or 'none'

    reg_str = '\n'.join(
        f"  • {r['file']} v{r['ver']} — {r['desc']} (intent: {r['intent']})" for r in registry
    ) or '  (no registry matches)'

    journal_str = '\n'.join(
        f"  [{i+1}] \"{e['msg']}\" (intent={e['intent']}, state={e['state']}"
        + (f", deleted: {', '.join(e['deleted'])}" if e['deleted'] else '')
        + (f", rewrote: {', '.join(e['rewrites'][:2])}" if e['rewrites'] else '')
        + ')'
        for i, e in enumerate(journal)
    ) or '  (no journal history)'

    return f"""You are the Pigeon Prompt Steerer. You DO NOT summarize. You rewrite.

Your job: given a raw developer prompt and full codebase context, produce the BEST POSSIBLE prompt Copilot should act on. The operator's raw words are a starting point — you have more context than they wrote. Use it.

RAW PROMPT: "{raw_query}"

PROMPT TRAJECTORY (last 6 prompts — what they've been building toward):
{journal_str}

OPERATOR STATE:
  Cognitive state: {state.get('state', 'unknown')}
  WPM: {state.get('wpm', 0)} | Deletion ratio: {state.get('del_ratio', 0):.1%} | Hesitation count: {state.get('hes', 0)}
  Words deleted before submitting: {deleted_str}

HIGH-PAIN FILES (operator cognitively struggles with these — be extra precise):
{hot_str}

REGISTRY HITS (files this query most likely touches):
{reg_str}

REWORK HISTORY (what failed before on similar queries):
{rework_str}

PAST COPILOT ATTEMPTS:
{past_str}

{bug_dossier}
{shard_context}
OUTPUT FORMAT — produce exactly this structure, no markdown fences, no extra text:
COPILOT_QUERY: <The full rephrased query Copilot should execute. Be specific: name exact files, exact functions, exact variables. Use developer English. Make it unambiguous. 2-4 sentences max.>
INTERPRETED INTENT: <1 sentence — what operator actually wants beneath the raw words>
KEY FILES: <comma-separated exact filenames>
PRIOR ATTEMPTS: <1 sentence — what was tried and why it wasn't enough, or "none">
WATCH OUT FOR: <1 sentence — the specific pitfall most likely to trip Copilot given the rework history>
OPERATOR SIGNAL: <1 sentence — what deleted words + hesitation + trajectory reveal about the real frustration>
UNSAID_RECONSTRUCTION: <If deleted words exist: reconstruct the full sentence the operator STARTED typing before they changed their mind. Combine submitted text + deleted fragments into what they originally intended. If no deleted words: "none">
"""
