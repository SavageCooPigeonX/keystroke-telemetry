"""codebase_transmuter_narrator_seq008_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 008 | VER: v001 | 118 lines | ~1,064 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import ast
import re
import time

def _narrate_file(filepath, profile, telem_entry=None):
    name = filepath.stem
    funcs = profile['functions']
    classes = profile['classes']
    imports = profile['imports']
    lines_count = profile['lines']
    tokens = profile['tokens']
    doc = profile['module_doc']
    t = telem_entry or {}

    parts = []

    # ─── IDENTITY ───
    parts.append(f'# {name}')
    mood = t.get('mood', 'chill')
    danger = t.get('danger', 0)
    touches = t.get('T', 0)
    parts.append(f'# V=[H={t.get("H",0):.2f} R={t.get("R",0):.2f} '
                 f'E={t.get("E",0):.2f} C={t.get("C",0):.2f} '
                 f'B={t.get("B",0)} T={touches} D={danger:.2f}]')
    parts.append(f'# {lines_count} lines / {tokens} tokens / mood: {mood}')
    parts.append('')

    # ─── PERSONALITY (from telemetry vector) ───
    intro = MOOD_INTROS.get(mood, MOOD_INTROS['chill'])
    parts.append(f'# {intro.format(T=touches, lines=lines_count)}')
    parts.append('')

    # entropy shedding note
    H = t.get('H', 0)
    if H > 0.3:
        parts.append(f'# ENTROPY WARNING: H={H:.2f} — copilot hedges hard on me.')
        parts.append('# every response about me is full of "maybe" and "probably".')
    elif H > 0.15:
        parts.append(f'# mild entropy: H={H:.2f} — copilot second-guesses sometimes.')

    # heat (operator hesitation)
    E = t.get('E', 0)
    if E > 0.5:
        parts.append(f'# OPERATOR HEAT: E={E:.2f} — the human hesitates when typing about me.')
        parts.append("# they're afraid. which means i'm important. or broken. both?")
    parts.append('')

    # ─── DEMONS (from bugs) ───
    demons = t.get('demons', [])
    if demons:
        parts.append('# ─── MY DEMONS ───')
        for demon_str in demons:
            bug_key = demon_str.split(':')[0] if ':' in demon_str else demon_str
            template = DEMON_TEMPLATES.get(bug_key,
                       f"THE {bug_key.upper()} — a bug lives in me. its name is {demon_str}.")
            parts.append(f'# {template.format(lines=lines_count)}')
        parts.append('')

    # ─── WHAT I SAY ABOUT MYSELF ───
    if doc:
        parts.append(f'# what i say about myself: "{doc[:120]}"')
    else:
        parts.append('# no docstring. i let my code speak. or scream.')
    parts.append('')

    # ─── WHO I TALK TO ───
    if imports:
        talkers = []
        for imp in imports[:8]:
            mod = imp.replace('from ', '').replace('import ', '').split(' ')[0]
            talkers.append(mod)
        parts.append(f'# talks to: {", ".join(talkers)}')
    else:
        parts.append('# talks to nobody. lone wolf.')
    parts.append('')

    # ─── WHAT I DO ───
    if funcs:
        pub = [f for f in funcs if not f['name'].startswith('_')]
        priv = [f for f in funcs if f['name'].startswith('_')]
        parts.append(f'# {len(pub)} public function(s), {len(priv)} private')

        for f in pub[:5]:
            args_s = ', '.join(f['args'][:4])
            doc_s = f' — "{f["doc"][:60]}"' if f['doc'] else ''
            parts.append(f'# - {f["name"]}({args_s}){doc_s}')

        if len(pub) > 5:
            parts.append(f'# ... and {len(pub) - 5} more')

        if priv:
            parts.append(f'# private workforce: {", ".join(p["name"] for p in priv[:6])}')
    else:
        parts.append('# no functions. i am a declaration of intent.')
    parts.append('')

    # ─── SIZE PERSONALITY ───
    if lines_count > 200:
        parts.append(f'# I AM {lines_count} LINES. I have eaten past the cap.')
        parts.append('# the compiler wants to split me. i will not go quietly.')
    elif lines_count < 20:
        parts.append('# tiny. almost a haiku. a constants file or a witness.')
    parts.append('')

    if profile['has_main']:
        parts.append('# has a __main__ block. i run solo when i want to.')

    # ─── SKELETON (actual structure) ───
    parts.append('')
    parts.append('# ─── STRUCTURE ───')
    for f in funcs:
        args_s = ', '.join(f['args'][:6])
        parts.append(f'def {f["name"]}({args_s}): ...')
    for c in classes:
        parts.append(f'class {c["name"]}: ...')

    return '\n'.join(parts)
