"""dynamic_prompt_seq017_build_context_main_seq011_v001.py — Auto-extracted by Pigeon Compiler."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import json, re, subprocess

def build_task_context(root):
    root = Path(root)
    now = datetime.now(timezone.utc)
    history = _profile_history(root)
    comps = _jsonl(root / 'logs' / 'prompt_compositions.jsonl', n=12)
    coms = _commits(root, n=8)
    focus = _task_focus(coms)
    unsaid = _unsaid(comps)
    hot = _hot_modules(root)
    rw = _rework(root)
    traj = _trajectory(root)
    watchlist, assumptions = _narrative_risks(root)
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
         f'**Cognitive state:** `{dom}` (WPM: {wpm} | Del: {dl}% | Hes: {hes})', '',
         f'> **CoT directive:** {_COT.get(dom, "Standard mode. Be thorough and structured.")}', '']
    if unsaid:
        L += ['### Unsaid Threads', "*Deleted from prompts \u2014 operator wanted this but didn't ask:*"]
        L += [f'- "{t}"' for t in unsaid] + ['']
    if hot:
        L += ['### Module Hot Zones', '*High cognitive load \u2014 take extra care with these files:*']
        L += [f'- `{m["m"]}` (hes={m["h"]}' + (f', {m["x"]} AI misses' if m["x"] else '') + ')' for m in hot] + ['']
    if rw and rw.get('rate', 0) > 0:
        L += ['### AI Rework Surface', f'*Miss rate: {rw["rate"]}% ({rw["n"]} responses)*']
        L += [f'- Failed on: "{w}"' for w in rw.get('worst', [])] + ['']
    if coms:
        real = [c for c in coms if '[pigeon-auto]' not in c['msg']][:4]
        if real:
            L += ['### Recent Work'] + [f'- `{c["hash"]}` {c["msg"]}' for c in real] + ['']
    if coaching:
        L += ['### Coaching Directives',
              '*LLM-synthesized behavioral rules for this operator:*']
        L += [f'- **{c}**' for c in coaching] + ['']
    if watchlist or assumptions:
        L += ['### Fragile Contracts',
              '*From push narratives — assumptions that could break:*']
        L += [f'- {r}' for r in watchlist]
        L += [f'- {a}' for a in assumptions]
        L += ['']
    if fixes:
        L += ['### Known Issues',
              '*From self-fix scanner — fix when touching nearby code:*']
        L += [f'- {f}' for f in fixes] + ['']
    if gaps:
        L += ['### Persistent Gaps',
              '*Recurring queries — operator keeps hitting these:*']
        L += [f'- [{g["n"]}x] {g["q"]}' for g in gaps] + ['']
    if traj and traj.get('n', 0) > 5:
        L += ['### Prompt Evolution',
              f'*This prompt has mutated {traj["n"]}x ({traj["l0"]}\u2192{traj["l1"]} lines). '
              f'Features added: {", ".join(traj["feat"]) or "none"}.*', '']
    # File consciousness — dating profiles + fears
    cons = _file_consciousness(root)
    if cons:
        L += [cons, '']
    L.append('<!-- /pigeon:task-context -->')
    return '\n'.join(L)
