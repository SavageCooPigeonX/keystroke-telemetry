"""Dynamic task-aware prompt injection — steers Copilot CoT from live signals."""

import json, re, subprocess
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter

def _jsonl(path, n=0):
    if not path.exists(): return []
    ll = path.read_text(encoding='utf-8', errors='ignore').strip().splitlines()
    if n: ll = ll[-n:]
    out = []
    for l in ll:
        try: out.append(json.loads(l))
        except Exception: pass
    return out

def _json(path):
    if not path.exists(): return None
    try: return json.loads(path.read_text(encoding='utf-8', errors='ignore'))
    except Exception: return None

def _profile_history(root):
    p = root / 'operator_profile.md'
    if not p.exists(): return []
    m = re.search(r'<!--\s*\n?DATA\s*\n(.*?)\nDATA\s*\n-->',
                  p.read_text(encoding='utf-8', errors='ignore'), re.DOTALL)
    if not m: return []
    try: return json.loads(m.group(1).strip()).get('history', [])
    except Exception: return []

def _commits(root, n=8):
    try:
        r = subprocess.run(['git', 'log', f'-{n}', '--pretty=format:%h|%s'],
                           capture_output=True, text=True, cwd=str(root), timeout=5)
        return [{'hash': p[0], 'msg': p[1]} for line in r.stdout.strip().splitlines()
                if len(p := line.split('|', 1)) == 2]
    except Exception: return []

def _task_focus(commits):
    msgs = [c['msg'] for c in commits[:5] if '[pigeon-auto]' not in c['msg']]
    if not msgs: return 'unknown'
    w = ' '.join(msgs).lower()
    for kw, label in [
        (('fix', 'bug', 'broken', 'error'), 'debugging / fixing'),
        (('feat', 'add', 'build', 'implement'), 'building new features'),
        (('refactor', 'clean', 'rename', 'split'), 'refactoring / restructuring'),
        (('doc', 'readme', 'manifest'), 'documentation / organization'),
        (('test', 'verify', 'check'), 'testing / validation'),
    ]:
        if any(k in w for k in kw): return label
    return msgs[0][:50]

def _unsaid(comps):
    threads = []
    for c in comps[-8:]:
        for w in (c.get('deleted_words') or []):
            word = w.get('word', w) if isinstance(w, dict) else str(w)
            if word and len(word) > 3: threads.append(word)
    return threads[-6:]

def _hot_modules(root):
    raw = _json(root / 'file_heat_map.json')
    if not raw or not isinstance(raw, dict): return []
    items = []
    for name, v in raw.items():
        if not isinstance(v, dict): continue
        samp = v.get('samples', [])
        if isinstance(samp, list):
            n = len(samp)
            if n < 2: continue
            hes = round(sum(s.get('hes', 0) for s in samp) / n, 3)
            miss = sum(1 for s in samp if s.get('verdict') == 'miss')
        else:
            n = samp
            if n < 2: continue
            hes = round(v.get('total_hes', 0) / max(n, 1), 3)
            miss = v.get('miss_count', 0)
        if hes > 0.4 or miss > 0:
            items.append({'m': name, 'h': hes, 'x': miss})
    return sorted(items, key=lambda x: x['h'], reverse=True)[:5]

def _rework(root):
    raw = _json(root / 'rework_log.json')
    if not raw: return {}
    entries = raw if isinstance(raw, list) else raw.get('entries', [])
    if not entries: return {}
    misses = [e for e in entries if e.get('verdict') == 'miss']
    return {'rate': round(len(misses) / max(len(entries), 1) * 100, 1),
            'n': len(entries),
            'worst': [e.get('query_text', '')[:60] for e in
                      sorted(misses, key=lambda e: e.get('rework_score', 0),
                             reverse=True)[:3]]}

def _trajectory(root):
    raw = _json(root / 'logs' / 'copilot_prompt_mutations.json')
    if not raw: return {}
    snaps = raw.get('snapshots', [])
    if len(snaps) < 2: return {}
    first, last = snaps[0], snaps[-1]
    gained = [k for k, v in last.get('features', {}).items()
              if v and not first.get('features', {}).get(k)]
    return {'n': len(snaps), 'l0': first.get('lines', 0),
            'l1': last.get('lines', 0), 'feat': gained}

def _narrative_risks(root):
    d = root / 'docs' / 'push_narratives'
    if not d.exists(): return [], []
    files = sorted(d.glob('*.md'), reverse=True)[:3]
    if not files: return [], []
    watchlist, assumptions = [], []
    for f in files:
        text = f.read_text(encoding='utf-8', errors='ignore')
        for line in text.splitlines():
            l = line.strip()
            if l.upper().startswith('REGRESSION WATCHLIST'):
                watchlist.extend(r.strip() for r in l.split(':', 1)[-1].split(',') if r.strip())
            if 'assumes' in l.lower() and '—' in l and not l.startswith('**'):
                assumptions.append(l[:120])
            elif l.startswith('**') and 'speaks:' in l:
                assumptions.append(l[:120])
            elif l.startswith('**') and 'was touched' in l:
                assumptions.append(l[:120])
    return watchlist[:5], assumptions[:6]

def _self_fix_crit(root):
    d = root / 'docs' / 'self_fix'
    if not d.exists(): return []
    files = sorted(d.glob('*.md'), reverse=True)
    if not files: return []
    lines = files[0].read_text(encoding='utf-8', errors='ignore').splitlines()
    items = []
    for i, line in enumerate(lines):
        if '[CRITICAL]' in line or '[HIGH]' in line:
            sev = '[CRITICAL]' if '[CRITICAL]' in line else '[HIGH]'
            kind = re.sub(r'^.*\]\s*', '', line.strip())
            fline = next((l for l in lines[i+1:i+4] if '**File**' in l), '')
            fname = re.sub(r'.*\*\*File\*\*:\s*', '', fline).strip()
            items.append(f'{sev} {kind}' + (f' in `{fname}`' if fname else ''))
    seen = set()
    return [x for x in items if not (x in seen or seen.add(x))][:5]

def _coaching(root):
    p = root / 'operator_coaching.md'
    if not p.exists(): return []
    text = p.read_text(encoding='utf-8', errors='ignore')
    bullets = []
    for line in text.splitlines():
        m = re.match(r'\s*\*\s*\*\*(.+?)\*\*', line)
        if m: bullets.append(m.group(1).rstrip(':'))
    return bullets[:5]

def _gaps(root):
    raw = _json(root / 'query_memory.json')
    if not raw: return []
    qs = raw.get('queries', raw if isinstance(raw, list) else [])
    fp = Counter(q.get('fingerprint', '') for q in qs
                 if q.get('fingerprint', '') not in ('', 'background')
                 and not q.get('fingerprint', '').startswith('bg'))
    return [{'q': f, 'n': n} for f, n in fp.most_common(4) if n >= 2]

def _file_consciousness(root):
    """Load file consciousness report from cached profiles, including slumber party warnings."""
    try:
        fp = root / 'file_profiles.json'
        if not fp.exists(): return ''
        profiles = json.loads(fp.read_text('utf-8'))
        if not profiles: return ''
        drama = sorted(profiles.items(), key=lambda x: x[1].get('version', 0), reverse=True)[:4]
        feared = {}
        for _, p in profiles.items():
            for f in p.get('fears', []):
                feared[f] = feared.get(f, 0) + 1
        top_fears = sorted(feared.items(), key=lambda x: x[1], reverse=True)[:3]
        lines = ['### File Consciousness', f'*{len(profiles)} modules profiled*']
        if drama:
            lines.append('\n**High-drama (most mutations):**')
            for name, p in drama:
                partners = p.get('partners', [])
                top_p = f' \u2194 {partners[0]["name"]}' if partners else ''
                lines.append(f'- `{name}` v{p["version"]}{top_p}')
        if top_fears:
            lines.append('\n**Codebase fears:**')
            for fear, count in top_fears:
                lines.append(f'- {fear} ({count} modules)')
        # Slumber party: surface high-score coupling warnings
        hot_couples = []
        for name, p in profiles.items():
            for partner in p.get('partners', []):
                if partner.get('score', 0) >= 0.45:
                    hot_couples.append((name, partner['name'], partner['score'], partner.get('reason', '')))
        hot_couples.sort(key=lambda x: x[2], reverse=True)
        if hot_couples:
            lines.append('\n**Slumber party warnings (high coupling):**')
            for a, b, score, reason in hot_couples[:3]:
                lines.append(f'- `{a}` ↔ `{b}` (score={score:.2f}, {reason})')
        return '\n'.join(lines)
    except Exception:
        return ''

def _codebase_health(root):
    """Load context_veins_seq001_v001.json and build a Codebase Health section for CoT injection."""
    vp = root / 'pigeon_brain' / 'context_veins_seq001_v001.json'
    if not vp.exists():
        return ''
    try:
        data = json.loads(vp.read_text('utf-8'))
    except Exception:
        return ''
    stats = data.get('stats', {})
    clots = data.get('clots', [])
    recs = data.get('trim_recommendations', [])
    arteries = data.get('arteries', [])
    if not clots and not recs:
        return ''
    lines = ['### Codebase Health (Veins / Clots)',
             f'*{stats.get("alive", 0)}/{stats.get("total_nodes", 0)} alive, '
             f'{stats.get("clots", 0)} clots, '
             f'avg vein health {stats.get("avg_vein_health", 0):.2f}*']
    if clots:
        lines.append('\n**Clots (dead/bloated — trim candidates):**')
        for c in clots[:6]:
            sigs = ', '.join(c.get('clot_signals', []))
            lines.append(f'- `{c["module"]}` (score={c["clot_score"]:.2f}): {sigs}')
    if recs:
        lines.append('\n**Self-trim recommendations:**')
        for r in recs[:4]:
            lines.append(f'- [{r["action"]}] `{r["target"]}`: {r["reason"]}')
    if arteries:
        top_art = [a for a in arteries[:3] if a.get('vein_score', 0) >= 0.8]
        if top_art:
            lines.append('\n**Critical arteries (do NOT break):**')
            for a in top_art:
                lines.append(f'- `{a["module"]}` (vein={a["vein_score"]:.2f}, in={a["in_degree"]})')
    return '\n'.join(lines)

_COT = {
    'frustrated': 'Operator is frustrated. Think step-by-step but keep output SHORT. Lead with the fix. Skip explanations unless asked. If unsure, say so in one line then give your best option.',
    'hesitant':   'Operator is uncertain. Think through what they MIGHT mean. Offer 2 interpretations and address both. End with a clarifying question.',
    'flow':       'Operator is in flow. Match their speed \u2014 technical depth, no preamble. Assume expertise. Go deeper than they asked.',
    'restructuring': 'Operator is rewriting/restructuring. Be precise. Use numbered steps and headers. Match the effort they put into their prompt.',
    'abandoned':  'Operator previously abandoned a message. They may be re-approaching. Be direct and welcoming.',
}

# ── Provenance gate: what feeds the CoT directive ──
# MEASURED fields → allowed to drive behavioral changes (state, thresholds)
# DERIVED fields → displayed as "system's current theory", not used for CoT selection
_MEASURED_INPUTS = frozenset({
    'wpm', 'deletion_ratio', 'hesitation_count', 'chars_per_sec',
    'rewrite_count', 'total_keystrokes', 'duration_ms',
    'typo_corrections', 'intentional_deletions',
})
_DERIVED_INPUTS = frozenset({
    'coaching', 'unsaid', 'narrative_risks', 'self_fix_crit',
    'trajectory', 'gaps', 'file_consciousness', 'codebase_health',
})

def _strip_task_context_blocks(text: str) -> str:
    pat = re.compile(
        r'(?ms)^\s*<!-- pigeon:task-context -->\s*$\n.*?^\s*<!-- /pigeon:task-context -->\s*$\n?',
    )
    return pat.sub('', text).rstrip() + '\n'


def _find_task_context_anchor(text: str) -> int:
    for marker in (
        '<!-- pigeon:task-queue -->',
        '<!-- pigeon:operator-state -->',
        '<!-- pigeon:prompt-telemetry -->',
        '<!-- pigeon:auto-index -->',
    ):
        idx = text.find(marker)
        if idx >= 0:
            return idx
    return -1

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
         f'**Cognitive state:** `{dom}` (WPM: {wpm} | Del: {dl}% | Hes: {hes})'
         f' · *[source: measured]*', '',
         f'> **CoT directive:** {_COT.get(dom, "Standard mode. Be thorough and structured.")}', '']
    if unsaid:
        L += ['### Unsaid Threads', "*Deleted from prompts \u2014 operator wanted this but didn't ask:*"]
        L += [f'- "{t}"' for t in unsaid] + ['']
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
    if coaching:
        L += ['### Coaching Directives *[source: llm_derived]*',
              '*LLM-synthesized behavioral rules \u2014 treat as hypothesis, not measurement:*']
        L += [f'- **{c}**' for c in coaching] + ['']
    if watchlist or assumptions:
        L += ['### Fragile Contracts *[source: llm_derived]*',
              '*From push narratives (LLM-generated) \u2014 treat as hypothesis:*']
        L += [f'- {r}' for r in watchlist]
        L += [f'- {a}' for a in assumptions]
        L += ['']
    if fixes:
        L += ['### Known Issues *[source: measured]*',
              '*From self-fix scanner (AST-verified) \u2014 fix when touching nearby code:*']
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
    # Codebase health — veins/clots from context_veins_seq001_v001.json
    health = _codebase_health(root)
    if health:
        L += [health, '']
    L.append('<!-- /pigeon:task-context -->')
    return '\n'.join(L)

def inject_task_context(root):
    root = Path(root)
    cp = root / '.github' / 'copilot-instructions.md'
    if not cp.exists(): return False
    block = build_task_context(root)
    text = _strip_task_context_blocks(cp.read_text(encoding='utf-8'))
    idx = _find_task_context_anchor(text)
    if idx >= 0:
        text = text[:idx].rstrip() + '\n\n' + block + '\n\n' + text[idx:].lstrip()
    else:
        text = text.rstrip() + '\n\n---\n\n' + block + '\n'
    cp.write_text(text, encoding='utf-8')
    return True

if __name__ == '__main__':
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    print(build_task_context(root))
    ok = inject_task_context(root)
    print(f'\nInjected: {ok}')
