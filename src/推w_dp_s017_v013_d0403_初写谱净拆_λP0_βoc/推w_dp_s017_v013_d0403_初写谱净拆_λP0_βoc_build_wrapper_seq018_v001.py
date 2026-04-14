"""推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_build_wrapper_seq018_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 018 | VER: v001 | 118 lines | ~1,480 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import json, re, subprocess

def build_task_context(root):
    root = Path(root)
    now = datetime.now(timezone.utc)
    # Dossier routing: if high confidence, slim irrelevant sections
    dossier_conf, dossier_mods, dossier_bugs = _active_dossier_signal(root)
    slim_mode = dossier_conf >= 0.7
    history = _profile_history(root)
    comps = _jsonl(root / 'logs' / 'chat_compositions.jsonl', n=12)
    coms = _commits(root, n=8)
    focus = _task_focus(coms)
    unsaid = _unsaid(root, comps)
    unsaid_recons = _unsaid_reconstructions(root, unsaid)
    hot = _hot_modules(root)
    rw = _rework(root)
    traj = _trajectory(root) if not slim_mode else None
    watchlist, assumptions = _narrative_risks(root) if not slim_mode else ([], [])
    fixes = _self_fix_crit(root)
    coaching = _coaching(root)
    gaps = _gaps(root)
    rec = history[-5:] if history else []
    if rec:
        st = Counter(r.get('state', 'neutral') for r in rec)
        dom = st.most_common(1)[0][0]
        wpm = round(sum(r['wpm'] for r in rec) / len(rec), 1)
        hes = round(sum(r['hesitation'] for r in rec) / len(rec), 3)
        dl = round(sum(r['del_ratio'] for r in rec) / len(rec) * 100, 1)
    else:
        dom, wpm, hes, dl = 'neutral', 0, 0, 0

    L = ['<!-- pigeon:task-context -->', '## Live Task Context', '',
         f'*Auto-injected {now.strftime("%Y-%m-%d %H:%M UTC")} \u00b7 '
         f'{len(history)} messages profiled \u00b7 {len(coms)} recent commits*', '',
         f'**Current focus:** {focus}',
         f'**Cognitive state:** `{dom}` (WPM: {wpm} | Del: {dl}% | Hes: {hes})'
         f' · *[source: measured]*', '']
    # Per-prompt composition timing
    chat_comps = _jsonl(root / 'logs' / 'chat_compositions.jsonl', n=5)
    recent_durs = [int(c['duration_ms']) for c in chat_comps if c.get('duration_ms', 0) > 0]
    if recent_durs:
        avg_dur = round(sum(recent_durs) / len(recent_durs))
        L.append(f'**Prompt ms:** {", ".join(str(d) for d in recent_durs)} (avg {avg_dur}ms)')
        L.append('')
    L += [f'> **CoT directive:** {_COT.get(dom, "Standard mode. Be thorough and structured.")}', '']
    if unsaid or unsaid_recons:
        L += ['### Unsaid Threads', "*Deleted from prompts \u2014 operator wanted this but didn't ask:*"]
        if unsaid_recons:
            for r in unsaid_recons[-3:]:
                dw = ', '.join(r.get('deleted_words', []))
                tc = r.get('thought_completion', r.get('reconstructed_intent', ''))
                dr = r.get('deletion_reason', '')
                L.append(f'- **Reconstructed intent:** {tc}')
                L.append(f'  - *(deleted: {dw} | ratio: {r.get("deletion_ratio", 0):.0%})*')
            L.append('')
        if unsaid:
            L += [f'- "{t}"' for t in unsaid]
        L.append('')
    if hot:
        L += ['### Module Hot Zones *[source: measured]*', '*High cognitive load (from typing signal) \u2014 take extra care with these files:*']
        L += [f'- `{m["m"]}` (hes={m["h"]}' + (f', {m["x"]} AI misses' if m["x"] else '') + ')' for m in hot] + ['']
    if rw and rw.get('rate', 0) > 0:
        L += ['### AI Rework Surface', f'*Miss rate: {rw["rate"]}% ({rw["n"]} responses)*']
        L += [f'- Failed on: "{w}"' for w in rw.get('worst', [])] + ['']
    if coms:
        real = [c for c in coms if '[pigeon-auto]' not in c['msg']][:4]
        if real:
            L += ['### Recent Work'] + [f'- `{c["hash"]}` {c["msg"]}' for c in real] + ['']
    if coaching and not slim_mode:
        L += ['### Coaching Directives *[source: llm_derived]*',
              '*LLM-synthesized behavioral rules — treat as hypothesis, not measurement:*']
        L += [f'- **{c}**' for c in coaching] + ['']
    if watchlist or assumptions:
        L += ['### Fragile Contracts *[source: llm_derived]*',
              '*From push narratives (LLM-generated) — treat as hypothesis:*']
        L += [f'- {r}' for r in watchlist]
        L += [f'- {a}' for a in assumptions]
        L += ['']
    if fixes:
        L += ['### Known Issues *[source: measured]*',
              '*From self-fix scanner (AST-verified) — fix when touching nearby code:*']
        L += [f'- {f}' for f in fixes] + ['']
    if gaps and not slim_mode:
        L += ['### Persistent Gaps',
              '*Recurring queries — operator keeps hitting these:*']
        L += [f'- [{g["n"]}x] {g["q"]}' for g in gaps] + ['']
    if traj and traj.get('n', 0) > 5:
        L += ['### Prompt Evolution',
              f'*This prompt has mutated {traj["n"]}x ({traj["l0"]}\u2192{traj["l1"]} lines). '
              f'Features added: {", ".join(traj["feat"]) or "none"}.*', '']
    # Heavy sections: skip in slim mode (dossier-focused prompt)
    if not slim_mode:
        # Mutation effectiveness — which prompt sections actually help
        mut_eff = _mutation_effectiveness(root)
        if mut_eff:
            L += [mut_eff, '']
        # File consciousness — dating profiles + fears
        cons = _file_consciousness(root)
        if cons:
            L += [cons, '']
    # Codebase health — veins/clots from context_veins.json (always show)
    health = _codebase_health(root)
    if health:
        L += [health, '']
    # Slim mode indicator
    if slim_mode:
        L += [f'> **🎯 Dossier routing active** (conf={dossier_conf:.2f}). '
              f'Focus: {", ".join(dossier_mods[:3])}. '
              f'Bugs: {", ".join(dossier_bugs)}. '
              f'Sections trimmed: coaching, gaps, mutation effectiveness, file consciousness.', '']
    # Hooks are now injected as their own managed block (<!-- pigeon:hooks -->)
    # No longer embedded inside task-context
    L.append('<!-- /pigeon:task-context -->')
    return '\n'.join(L)
