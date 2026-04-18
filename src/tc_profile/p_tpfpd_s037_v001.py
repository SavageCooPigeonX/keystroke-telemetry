"""tc_profile_seq001_v001_format_profile_decomposed_seq037_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 037 | VER: v001 | 103 lines | ~1,259 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import Counter
import re

def format_profile_for_prompt(profile: dict | None = None) -> str:
    """Compress profile into a prompt injection block."""
    if profile is None:
        profile = load_profile()
    s = profile.get('shards', {})
    if not s or profile.get('samples', 0) < 5:
        return ''
    lines = ['OPERATOR PROFILE (learned from their typing history):']

    # voice
    v = s.get('voice', {})
    if v.get('top_words'):
        top5 = Counter(v['top_words']).most_common(8)
        lines.append(f'  VOICE: top words=[{", ".join(w for w,_ in top5)}] '
                     f'avg {v.get("avg_words_per_msg",0):.0f} words/msg '
                     f'caps={"yes" if v.get("uses_caps") else "never"}')
    if v.get('catchphrases'):
        lines.append(f'  CATCHPHRASES: {"; ".join(v["catchphrases"][:5])}')
    if v.get('filler_words'):
        top_fill = Counter(v['filler_words']).most_common(4)
        lines.append(f'  FILLERS: {", ".join(f"{w}({c}x)" for w,c in top_fill)}')

    # rhythm
    r = s.get('rhythm', {})
    if r.get('avg_wpm'):
        lines.append(f'  RHYTHM: {r["avg_wpm"]:.0f} WPM (p25={r.get("wpm_p25",0):.0f} '
                     f'p75={r.get("wpm_p75",0):.0f}) del_ratio={r.get("avg_del_ratio",0):.1%} '
                     f'peak_hours={r.get("peak_hours_utc",[])}')

    # deletions — the unsaid mind
    d = s.get('deletions', {})
    if d.get('top_unsaid'):
        lines.append(f'  UNSAID MIND: they delete these words most: {", ".join(d["top_unsaid"][:6])}')
    if d.get('deleted_words'):
        top_del = Counter(d['deleted_words']).most_common(5)
        lines.append(f'  DELETE PATTERNS: {", ".join(f"{w}({c}x)" for w,c in top_del)}')

    # topics
    t = s.get('topics', {})
    if t.get('recurring_themes'):
        themes = Counter(t['recurring_themes']).most_common(5)
        lines.append(f'  OBSESSIONS: {", ".join(f"{th}({c}x)" for th,c in themes)}')
    if t.get('module_mentions'):
        mods = Counter(t['module_mentions']).most_common(6)
        lines.append(f'  MODULE FOCUS: {", ".join(f"{m}({c})" for m,c in mods)}')
    if t.get('recent_focus'):
        lines.append(f'  RECENT FOCUS: {" → ".join(t["recent_focus"][-3:])}')

    # decisions
    dec = s.get('decisions', {})
    if dec.get('total_completions'):
        lines.append(f'  DECISIONS: {dec["accept_rate"]:.0%} accept rate '
                     f'({dec["total_completions"]} total) '
                     f'reward={dec["reward_rate"]:.0%} '
                     f'sweet_spot={dec.get("sweet_spot_len",0):.0f} chars')

    # emotions
    emo = s.get('emotions', {})
    if emo.get('state_distribution'):
        total_states = sum(emo['state_distribution'].values())
        top_states = Counter(emo['state_distribution']).most_common(4)
        state_str = ', '.join(f'{st}={c/total_states:.0%}' for st, c in top_states)
        lines.append(f'  EMOTIONS: {state_str} avg_hes={emo.get("avg_hesitation",0):.2f}')

    # predictions — what works for THIS operator
    pred = s.get('predictions', {})
    if pred.get('working_templates'):
        lines.append(f'  WHAT WORKS ({len(pred["working_templates"])} templates):')
        for t in pred['working_templates'][-3:]:
            lines.append(f'    ★ "{t["buf_tail"][-30:]}" → "{t["comp_head"][:40]}"')
    if pred.get('dead_templates'):
        lines.append(f'  WHAT FAILS ({len(pred["dead_templates"])} anti-patterns):')
        for t in pred['dead_templates'][-2:]:
            lines.append(f'    ✗ "{t["buf_tail"][-30:]}" → "{t["comp_head"][:30]}"')

    # code style — how they write code
    cs = s.get('code_style', {})
    if cs.get('top_imports'):
        lines.append(f'  CODE DNA: quotes={cs["preferred_quotes"]} '
                     f'hints={"yes" if cs.get("uses_type_hints") else "no"} '
                     f'imports={cs.get("import_style","?")} '
                     f'naming={cs.get("naming_convention","?")} '
                     f'avg_func={cs.get("avg_func_length",0):.0f}lines '
                     f'docstrings={cs.get("docstring_rate",0):.0%} '
                     f'fstrings={cs.get("fstring_rate",0):.0%}')
        lines.append(f'  TOP IMPORTS: {", ".join(cs["top_imports"][:8])}')
        if cs.get('top_decorators'):
            lines.append(f'  DECORATORS: {", ".join(cs["top_decorators"][:5])}')
        if cs.get('error_handling_style'):
            lines.append(f'  ERROR STYLE: {cs["error_handling_style"]} '
                         f'exceptions=[{", ".join(cs.get("top_exceptions",[])[:4])}]')
        if cs.get('func_name_samples'):
            lines.append(f'  FUNC NAMES: {", ".join(cs["func_name_samples"][:10])}')

    if len(lines) <= 1:
        return ''
    lines.append('  USE this profile to write AS THEM. Match their vocabulary, rhythm, obsessions.')
    lines.append('  For CODE mode: match their quote style, naming, import patterns, error handling.')
    return '\n'.join(lines)
