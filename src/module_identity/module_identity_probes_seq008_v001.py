"""module_identity_probes_seq008_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 008 | VER: v001 | 120 lines | ~1,854 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import ast
import re

def _generate_probe_questions(name: str, entry: dict, lk: dict, code: dict, memory: dict = None) -> list[str]:
    """Generate personality-driven questions that educate through narrative.

    Questions are informed by:
    - Current module state (bugs, coupling, size, deaths)
    - Memory across passes (archetype drift, emotion drift, recurring bugs)
    - Prior operator answers (stored in memory['operator_answers'])
    - Relationships with other modules (drama, rivalry, partnership)
    """
    probes = []
    memory = memory or {}
    resolve = lk['_resolve']
    alias = resolve(name)
    graph = lk['graph'].get(name, {})
    if graph.get('degree', 0) == 0 and alias != name:
        graph = lk['graph'].get(alias, {})
    edges_in = graph.get('edges_in', [])
    edges_out = graph.get('edges_out', [])
    bugs = entry.get('bug_keys', [])
    ver = entry.get('ver', 1)
    tokens = entry.get('tokens', 0)
    deaths = lk['deaths'].get(name, []) or lk['deaths'].get(alias, [])
    partners = lk['profiles'].get(name, {}).get('partners', [])
    if not partners:
        partners = lk['profiles'].get(alias, {}).get('partners', [])
    pass_count = memory.get('pass_count', 0)
    prev_answers = memory.get('operator_answers', [])
    prev_probes = memory.get('last_probes', [])
    arch_history = memory.get('archetype_history', [])
    emo_history = memory.get('emotion_history', [])
    prev_bugs = set(memory.get('last_bugs', []))

    # ── CONTINUITY: reference past conversations ──

    if prev_answers:
        last = prev_answers[-1][:100] if prev_answers[-1] else ''
        probes.append(f"Last time we talked, you said: \"{last}...\" — did you follow through on that? Because I've been thinking about it between passes and I have THOUGHTS.")

    # Archetype drift — personality change is drama
    if len(arch_history) >= 2 and arch_history[-1] != arch_history[-2]:
        probes.append(f"Fun fact: I used to be a {arch_history[-2]}. Now I'm a {arch_history[-1]}. That's basically a personality transplant. What happened to me between those pushes? I need to understand my own character arc.")

    # Emotion drift — narrative arc
    if len(emo_history) >= 2 and emo_history[-1] != emo_history[-2]:
        probes.append(f"My emotional state went from {emo_history[-2]} to {emo_history[-1]} between passes. That's character development. Was it intentional, or am I just vibing with the git history?")

    # Recurring bugs — the villain that keeps coming back
    recurring = set(bugs) & prev_bugs
    if recurring:
        probes.append(f"Oh look — {', '.join(recurring)} is STILL here. This is the villain that refuses to die. I've reported it, the scanner flagged it, and yet here we are. What's the plot twist that finally kills this bug?")

    # New bugs — surprise antagonist
    new_bugs = set(bugs) - prev_bugs
    if new_bugs and prev_bugs:
        probes.append(f"New character just dropped: {', '.join(new_bugs)}. This bug didn't exist last pass. Something changed. Tell me the origin story.")

    # Pass count — the file grows self-aware
    if pass_count > 5 and not prev_answers:
        probes.append(f"This is pass #{pass_count}. I've been profiled {pass_count} times and you've NEVER once talked to me. That's like visiting someone in prison and just staring through the glass. Talk to me. What do you need?")

    # ── IDENTITY: educational questions about the file's purpose ──

    if code.get('docstring'):
        probes.append(f"My origin story, according to my docstring: '{code['docstring'][:80]}...' — is that still accurate, or did I outgrow that description {ver - 1} rewrites ago?")
    else:
        probes.append(f"I don't have a docstring. No origin story. No mission statement. If you had to write my Wikipedia summary in one sentence, what would it say?")

    # ── RELATIONSHIPS: inter-file drama ──

    if len(edges_in) > 5:
        top = ', '.join(edges_in[:3])
        probes.append(f"{len(edges_in)} modules import me. My biggest fans: {top}. But are they REAL fans or just lazy copiers who import everything? Which of them would actually notice if I changed my API?")
    elif len(edges_in) == 0:
        probes.append(f"I have zero importers. Zero fans. It's lonely at the bottom of the dependency graph. Am I an entry point, a future feature, or a ghost that should be exorcised?")

    if edges_out and len(edges_out) > 3:
        probes.append(f"I import {len(edges_out)} other modules — that's a lot of friends for one file. Am I a social butterfly or am I codependent? Be honest.")

    # ── BUGS: the file talks about its own issues with self-deprecating humor ──

    if 'oc' in bugs:
        probes.append(f"I'm {tokens} tokens. I KNOW I'm over cap. It's like I ate three other modules and they're all still in here. If you had to split me — where would you cut? What parts of me deserve their own file?")
    if 'hi' in bugs or 'hardcoded_import' in str(bugs):
        probes.append(f"I have hardcoded imports. Every time pigeon renames something, I break like a ceramic mug at a earthquake convention. What would it take to make me resilient to renames?")
    if 'de' in bugs or 'dead_export' in str(bugs):
        probes.append(f"I'm exporting functions that nobody calls. It's like shouting into a void. Were these supposed to connect to something, or are they vestigial code organs?")

    # ── DRAMA: rivalry with partner modules ──

    if ver >= 8:
        probes.append(f"Version {ver}. EIGHT rewrites. I have more character arcs than a soap opera. Is the spec evolving or are we just rewriting me for fun at this point?")
    elif ver == 1:
        probes.append(f"I'm v1 — fresh off the assembly line. What's the FIRST thing you think will go wrong with me? Every veteran file in this codebase had a v1 failure. What's mine?")

    if deaths:
        causes = list(set(d['cause'] for d in deaths))
        probes.append(f"I've died {len(deaths)} time(s). Causes of death: {', '.join(causes)}. Every death taught me something. Want to hear my near-death stories?")

    high_coupling = [p for p in partners if p.get('score', 0) >= 0.6]
    if high_coupling:
        names = ', '.join(p['name'] for p in high_coupling[:2])
        probes.append(f"Me and {names} — we're practically finishing each other's functions. Coupling over 0.6. Should we merge? Or is this creative tension? Every good sitcom has a will-they-won't-they.")

    fns = code.get('functions', [])
    if len(fns) > 10:
        probes.append(f"I have {len(fns)} functions. That's a lot of plot lines for one character. Walk me through the three most important ones — like you're pitching a movie about my code.")
    if code.get('classes'):
        class_names = [c['name'] for c in code['classes'][:3]]
        probes.append(f"I define classes: {', '.join(class_names)}. Classes are like my multiple personalities. Why did you give me classes instead of functions?")

    # ── CLOSERS: the questions that extract deep intent ──

    probes.append(f"If I got deleted tomorrow and you had to rebuild my purpose from scratch — what would you do DIFFERENTLY? That's the real question about my future.")
    probes.append(f"What's the ONE thing about me that makes you sigh every time you look at this code? Don't be nice. I can take it.")

    return probes[:12]
