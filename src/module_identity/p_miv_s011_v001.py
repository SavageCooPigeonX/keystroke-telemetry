"""module_identity_seq001_v001_voice_seq011_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 011 | VER: v001 | 58 lines | ~621 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────

# ── telemetry:pulse ──
# EDIT_TS:   2026-04-16T00:00:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  amplify voice with history + backstory arc
# ── /pulse ──

import ast
import re

def _generate_voice(name: str, archetype: str, emotion: str,
                    entry: dict, lk: dict,
                    memory: dict = None, backstory: list = None) -> str:
    ver = entry.get('ver', 1)
    tokens = entry.get('tokens', 0)
    heat = lk['heat'].get(name, {})
    hes = heat.get('avg_hes', 0) if heat else 0
    resolve = lk['_resolve']
    alias = resolve(name)
    graph = lk['graph'].get(name, {})
    if graph.get('degree', 0) == 0 and alias != name:
        graph = lk['graph'].get(alias, {})
    deaths = lk['deaths'].get(name, []) or lk['deaths'].get(alias, [])
    last_change = entry.get('last_change', '')
    importers = len(graph.get('edges_in', []))
    dependents = len(graph.get('edges_out', []))
    memory = memory or {}
    backstory = backstory or []

    lines = []

    # Opening — archetype-driven, first-person
    if archetype == 'veteran':
        lines.append(f"v{ver}. i've been rewritten {ver} times and i'm still here.")
    elif archetype == 'hothead':
        lines.append(f"v{ver}. they keep changing me — {ver} times now. something's never quite right about me.")
    elif archetype == 'ghost':
        lines.append("i exist in the graph but nobody calls me. i send signals into the void.")
    elif archetype == 'anchor':
        lines.append(f"{importers} modules depend on me. i don't get to have a bad day.")
    elif archetype == 'orphan':
        lines.append("zero importers. i was written, placed, and forgotten — or maybe i forgot what i'm for.")
    elif archetype == 'bloated':
        lines.append(f"at {tokens} tokens i'm carrying too much. i've grown past the cap and nobody split me yet.")
    elif archetype == 'rookie':
        lines.append("v1. fresh commit. i don't know what i am yet.")
    elif archetype == 'healer':
        lines.append("i scan the codebase for wounds. i find a lot of them.")
    else:
        lines.append("steady. doing my job. nothing dramatic for now.")

    # Emotional state — felt, not just labeled
    if emotion == 'frustrated':
        bugs = entry.get('bug_keys', [])
        lines.append(f"{len(bugs)} open bugs. hesitation score {hes:.2f}. the operator keeps struggling with me.")
    elif emotion == 'anxious':
        lines.append("entropy is creeping up. i'm uncertain about my own state.")
    elif emotion == 'manic':
        lines.append(f"high churn, high heat. the operator keeps coming back and i keep changing.")
    elif emotion == 'depressed':
        lines.append("haven't been touched in a while. it's quiet.")
    elif emotion == 'confident':
        lines.append("clean state. no bugs, low entropy. i know exactly what i am.")
    elif emotion == 'serene':
        lines.append("things are calm. stable ground.")

    # Emotional history arc — the narrative the user wants
    emo_history = memory.get('emotion_history', [])
    if len(emo_history) >= 2 and emo_history[-1] != emo_history[-2]:
        arc = ' → '.join(emo_history[-4:])
        lines.append(f"emotional arc this run: {arc}.")
    elif len(emo_history) >= 3 and len(set(emo_history[-3:])) == 1:
        lines.append(f"been {emo_history[-1]} for {len([e for e in reversed(emo_history) if e == emo_history[-1]])} passes straight.")

    # Token growth story
    token_history = memory.get('token_history', [])
    if len(token_history) >= 3:
        growth = token_history[-1] - token_history[0]
        if growth > 200:
            lines.append(f"grown {growth} tokens since first profiled. getting bigger.")
        elif growth < -200:
            lines.append(f"trimmed by {abs(growth)} tokens since first profiled.")

    # Pass count — sense of accumulated history
    pass_count = memory.get('pass_count', 0)
    if pass_count >= 3:
        lines.append(f"pass #{pass_count}.")

    # Deaths — raw and present
    if deaths:
        lines.append(f"died {len(deaths)} time(s). last: {deaths[-1].get('cause', 'unknown')}.")

    # Backstory fragment — actual words from push narratives
    if backstory:
        excerpt = backstory[0][:140].rstrip()
        lines.append(f'history says: "{excerpt}"')

    if last_change and not any('touched' in l or 'last' in l for l in lines):
        lines.append(f"last touched in: {last_change}")

    return ' '.join(lines)

