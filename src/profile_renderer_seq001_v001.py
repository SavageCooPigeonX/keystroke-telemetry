"""profile_renderer_seq001_v001.py — Generate interactive profile pages for sentient modules.

Each module gets its own page at build/profiles/{name}.html containing:
  - Identity header (archetype label, emotion, voice)
  - Interactive wake-up: file greets operator, asks probing questions
  - Self-coaching: file explains its own code, weaknesses, relationships
  - Source code overview (functions, imports, structure)
  - Probe questions for intent extraction
  - Conversation area with localStorage persistence
  - Relationship graph (edges_in/out, partners, coupling)
  - Backstory, entropy, heat, self-diagnosis, TODO, memory
"""

import json
from pathlib import Path

PROFILES_DIR = 'build/profiles'

CSS = '''
:root {
  --bg:#0d1117;--card:#161b22;--border:#30363d;
  --text:#c9d1d9;--dim:#8b949e;--green:#3fb950;
  --orange:#d29922;--red:#f85149;--blue:#58a6ff;--purple:#bc8cff;
}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;background:var(--bg);color:var(--text);padding:20px;max-width:960px;margin:0 auto}
a{color:var(--blue);text-decoration:none}
a:hover{text-decoration:underline}
h1{font-size:28px;margin-bottom:4px}
h2{font-size:16px;color:var(--dim);margin:20px 0 10px;border-bottom:1px solid var(--border);padding-bottom:4px}
.subtitle{color:var(--dim);font-size:13px;margin-bottom:16px}
.dim{color:var(--dim);font-size:12px}

.hero{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:16px}
.hero-top{display:flex;align-items:center;gap:12px}
.hero-emoji{font-size:40px}
.hero-name{font-size:24px;font-weight:700}
.hero-sub{font-size:14px;color:var(--dim)}
.hero-badges{display:flex;gap:6px;margin-top:8px;flex-wrap:wrap}
.badge{font-size:11px;padding:2px 8px;border-radius:12px;border:1px solid var(--border)}
.badge.arch{color:var(--blue);border-color:var(--blue)}
.badge.emo{border-color:var(--purple)}
.badge.bug{color:var(--red);border-color:var(--red)}
.badge.ver{color:var(--green);border-color:var(--green)}
.badge.tok{color:var(--orange);border-color:var(--orange)}
.hero-voice{font-style:italic;font-size:14px;margin-top:10px;padding:8px 12px;background:var(--bg);border-radius:8px;border-left:3px solid var(--border);line-height:1.5}

.wake-up{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:20px;margin-bottom:16px;border-left:4px solid var(--red)}
.wake-msg{font-size:15px;line-height:1.7;margin-bottom:12px;white-space:pre-line;color:var(--text)}
.probe-section{margin-top:12px}
.probe-q{background:var(--bg);border:1px solid var(--red);border-radius:8px;padding:10px 14px;margin:6px 0;font-size:13px;line-height:1.5;cursor:pointer;transition:border-color .2s,background .2s}
.probe-q:hover{border-color:var(--orange);background:rgba(248,81,73,0.08)}
.probe-q::before{content:'\\1F6A8 ';font-size:14px}
.probe-q.answered{opacity:0.5;border-color:var(--green);background:transparent}
.probe-q.answered::before{content:'\\2705 '}

.coaching{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:16px}
.coach-item{font-size:13px;line-height:1.6;padding:4px 0;border-bottom:1px solid var(--border)}
.coach-item:last-child{border:none}
.coach-item::before{content:'\\1F4A1 ';font-size:12px}

.code-section{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:16px}
.fn-list{list-style:none;font-size:12px}
.fn-list li{padding:4px 0;border-bottom:1px solid var(--border);font-family:'Cascadia Code','Fira Code',monospace}
.fn-list li:last-child{border:none}
.fn-name{color:var(--blue)}
.fn-args{color:var(--dim)}
.fn-doc{color:var(--orange);font-style:italic;font-family:-apple-system,sans-serif}
.import-list{list-style:none;font-size:11px;color:var(--dim);font-family:monospace;columns:2}
.import-list li{padding:2px 0}

.convo{background:var(--card);border:1px solid var(--red);border-radius:12px;padding:16px;margin-bottom:16px;border-left:4px solid var(--red)}
.convo-log{max-height:400px;overflow-y:auto;margin-bottom:10px}
.convo-entry{font-size:12px;padding:6px 0;border-bottom:1px solid var(--border);line-height:1.5}
.convo-entry:last-child{border:none}
.convo-who{font-weight:600;font-size:11px}
.convo-who.file{color:var(--red)}
.convo-who.operator{color:var(--green)}
.convo-input{display:flex;gap:8px}
.convo-input textarea{flex:1;background:var(--bg);color:var(--text);border:1px solid var(--border);border-radius:6px;padding:8px;font-size:12px;resize:vertical;min-height:40px;font-family:inherit}
.convo-input button{background:var(--red);color:#fff;border:none;border-radius:6px;padding:8px 16px;cursor:pointer;font-size:12px;font-weight:600}
.convo-input button:hover{opacity:0.9}
.interrogation-stats{font-size:11px;color:var(--dim);margin-bottom:8px;display:flex;gap:12px}
.interrogation-stats span{color:var(--orange)}

.source-section{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:16px}
.source-pre{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:12px;overflow-x:auto;max-height:600px;overflow-y:auto;font-family:'Cascadia Code','Fira Code',monospace;font-size:11px;line-height:1.6;white-space:pre;color:var(--text);tab-size:4}

.notes-section{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:16px;border-left:4px solid var(--orange)}
.notes-section textarea{width:100%;background:var(--bg);color:var(--text);border:1px solid var(--border);border-radius:6px;padding:10px;font-size:12px;resize:vertical;min-height:80px;font-family:inherit;line-height:1.6}
.notes-section .notes-actions{display:flex;gap:8px;margin-top:8px;align-items:center}
.notes-section button{background:var(--orange);color:#000;border:none;border-radius:6px;padding:6px 14px;cursor:pointer;font-size:11px;font-weight:600}
.notes-saved{color:var(--green);font-size:11px;opacity:0;transition:opacity .3s}

.intent-export{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:16px}
.intent-export button{background:var(--purple);color:#fff;border:none;border-radius:6px;padding:8px 16px;cursor:pointer;font-size:12px;margin-right:8px}
.intent-export pre{background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px;margin-top:10px;font-size:11px;max-height:300px;overflow-y:auto;display:none;white-space:pre-wrap}

.grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px}
.box{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px}
.box h3{font-size:13px;color:var(--dim);margin-bottom:8px;text-transform:uppercase;letter-spacing:.5px}
.rel-list{list-style:none;font-size:12px}
.rel-list li{padding:3px 0;border-bottom:1px solid var(--border)}
.rel-list li:last-child{border:none}
.rel-in{color:var(--green)}
.rel-out{color:var(--orange)}

.backstory{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px;margin-bottom:12px}
.backstory-frag{font-size:12px;line-height:1.6;margin-bottom:10px;padding-left:12px;border-left:2px solid var(--border)}

.todo-list{list-style:none;font-size:12px}
.todo-list li{padding:4px 0;border-bottom:1px solid var(--border)}
.todo-list li::before{content:'\\25A1 ';color:var(--orange)}

.diag-list{list-style:none;font-size:12px}
.diag-list li{padding:3px 0;color:var(--orange)}
.diag-list li::before{content:'\\26A0 '}

.timeline{font-size:11px}
.timeline-entry{display:flex;gap:8px;padding:4px 0;border-bottom:1px solid var(--border)}
.timeline-ver{color:var(--blue);font-weight:600;min-width:28px}
.timeline-date{color:var(--dim);min-width:40px}
.timeline-desc{color:var(--text)}
.timeline-intent{color:var(--purple);font-size:10px}
.timeline-tokens{color:var(--dim);font-size:10px;margin-left:auto}

.memory{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px;margin-bottom:12px}
.mem-stat{display:inline-block;margin-right:16px;font-size:12px}
.mem-label{color:var(--dim)}
.mem-val{font-weight:600}

.partner-card{display:flex;align-items:center;gap:8px;padding:4px 0;border-bottom:1px solid var(--border);font-size:12px}
.partner-card:last-child{border:none}
.partner-score{font-weight:600;min-width:32px}
.partner-name{color:var(--blue)}
.partner-reason{color:var(--dim);font-size:11px}

.fear{font-size:12px;color:var(--red);padding:2px 0}
.fear::before{content:'\\26A1 '}

.nav{margin-bottom:16px;font-size:12px}

.section-toggle{cursor:pointer;user-select:none}
.section-toggle::after{content:' \\25BC';font-size:10px;color:var(--dim)}
.collapsed .section-body{display:none}
.collapsed .section-toggle::after{content:' \\25B6'}

@media(max-width:700px){.grid2{grid-template-columns:1fr}}
'''


def _sparkline_svg(values, w=120, h=28, color='#58a6ff'):
    if not values or len(values) < 2:
        return ''
    mn, mx = min(values), max(values)
    rng = mx - mn if mx != mn else 1
    step = w / (len(values) - 1)
    points = []
    for i, v in enumerate(values):
        x = round(i * step, 1)
        y = round(h - ((v - mn) / rng) * (h - 4) - 2, 1)
        points.append(f'{x},{y}')
    polyline = ' '.join(points)
    last_y = points[-1].split(',')[1]
    return (f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'style="vertical-align:middle">'
            f'<polyline points="{polyline}" fill="none" stroke="{color}" '
            f'stroke-width="1.5" stroke-linecap="round"/>'
            f'<circle cx="{w}" cy="{last_y}" r="2" fill="{color}"/>'
            f'</svg>')


def _esc(text):
    """HTML-escape text."""
    return str(text).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')


def _generate_wakeup_message(ident: dict) -> str:
    """Generate a data-driven opening — personality emerges from health signals."""
    name = ident['name']
    arch = ident['archetype']
    emo = ident['emotion']
    ver = ident['ver']
    tokens = ident['tokens']
    edges_in = ident.get('edges_in', [])
    bugs = ident.get('bugs', [])
    deaths = ident.get('deaths', [])
    partners = ident.get('partners', [])
    code = ident.get('code', {})
    fns = code.get('functions', [])

    lines = []

    # Identity line — archetype voice from data signals
    voice = {
        'veteran': f"v{ver}. {len(edges_in)} dependents. survived every rewrite.",
        'hothead': f"v{ver}. high churn. edited constantly.",
        'ghost': "zero importers. silent in the graph.",
        'anchor': f"{len(edges_in)} modules depend on me.",
        'orphan': "nobody imports me. maybe dead, maybe not.",
        'bloated': f"{tokens} tokens. should've been split ages ago.",
        'healer': "i scan for problems others create.",
        'rookie': "v1. just got here.",
        'stable': "no drama. doing my job.",
    }
    lines.append(f"{name} — {voice.get(arch, 'here.')}")

    # Emotion — one line from current health state
    emo_lines = {
        'frustrated': f"{len(bugs)} bugs keep coming back.",
        'anxious': "entropy climbing. uncertain.",
        'manic': "high churn, lots of attention right now.",
        'depressed': "untouched for a while. quiet.",
        'confident': "clean pass. no bugs.",
    }
    if emo in emo_lines:
        lines.append(emo_lines[emo])

    # Partners — brief coupling note
    if partners and partners[0].get('score', 0) >= 0.5:
        p = partners[0]
        lines.append(f"tightly coupled with {p['name']} ({p['score']:.2f}).")

    # Bugs / deaths — factual
    if bugs:
        lines.append(f"open bugs: {', '.join(bugs[:3])}.")
    if deaths:
        lines.append(f"died {len(deaths)}x. last: {deaths[-1].get('cause', '?')}.")

    # API hook
    if fns:
        public_fns = [f['name'] for f in fns if not f['name'].startswith('_')]
        if public_fns:
            lines.append(f"public api: {', '.join(public_fns[:3])}.")

    lines.append("what are you here about?")
    return ' '.join(lines)


def render_profile(ident: dict, root: Path) -> Path:
    """Render a single module's interactive profile page."""
    root = Path(root)
    out_dir = root / PROFILES_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    name = ident['name']
    cn = ident['cn_name']
    out_path = out_dir / f'{name}.html'

    # Wake-up message
    wakeup = _generate_wakeup_message(ident)

    # Probe questions HTML
    probes = ident.get('probes', [])
    probes_html = ''.join(
        f'<div class="probe-q" data-idx="{i}" onclick="answerProbe(this)">{_esc(q)}</div>'
        for i, q in enumerate(probes)
    )

    # Self-coaching HTML
    coaching = ident.get('coaching', [])
    coaching_html = ''.join(
        f'<div class="coach-item">{_esc(c)}</div>' for c in coaching
    )

    # Code skeleton
    code = ident.get('code', {})
    fns_html = ''
    for fn in code.get('functions', [])[:20]:
        args_str = ', '.join(fn.get('args', []))
        doc_str = f' <span class="fn-doc">— {_esc(fn["doc"][:80])}</span>' if fn.get('doc') else ''
        fns_html += f'<li><span class="fn-name">{_esc(fn["name"])}</span>(<span class="fn-args">{_esc(args_str)}</span>){doc_str}</li>'
    imports_html = ''.join(
        f'<li>{_esc(imp)}</li>' for imp in code.get('imports', [])[:15]
    )
    classes_html = ''
    for cls in code.get('classes', [])[:5]:
        methods = ', '.join(cls.get('methods', [])[:6])
        classes_html += f'<li><span class="fn-name">class {_esc(cls["name"])}</span> — methods: {_esc(methods)}</li>'

    # Relationship lists
    edges_in_html = ''
    for e in ident.get('edges_in', [])[:20]:
        link = f'<a href="{e}.html">{_esc(e)}</a>'
        edges_in_html += f'<li class="rel-in">\u2190 {link}</li>'
    if not edges_in_html:
        edges_in_html = '<li class="dim">no importers</li>'
    edges_out_html = ''
    for e in ident.get('edges_out', [])[:20]:
        link = f'<a href="{e}.html">{_esc(e)}</a>'
        edges_out_html += f'<li class="rel-out">\u2192 {link}</li>'
    if not edges_out_html:
        edges_out_html = '<li class="dim">no imports</li>'

    # Partners
    partners_html = ''
    for p in ident.get('partners', [])[:6]:
        score = p.get('score', 0)
        color = '#f85149' if score >= 0.7 else '#d29922' if score >= 0.4 else '#3fb950'
        pname = p.get('name', '')
        link = f'<a href="{pname}.html">{_esc(pname)}</a>'
        partners_html += (
            f'<div class="partner-card">'
            f'<span class="partner-score" style="color:{color}">{score:.2f}</span>'
            f'<span class="partner-name">{link}</span>'
            f'<span class="partner-reason">{_esc(p.get("reason", ""))}</span>'
            f'</div>'
        )
    fears_html = ''.join(
        f'<div class="fear">{_esc(f)}</div>' for f in ident.get('fears', [])[:5]
    )

    # Consciousness — function-level inner voice
    consciousness = ident.get('consciousness', {})
    cons_funcs = consciousness.get('functions', [])
    consciousness_html = ''
    if cons_funcs:
        ptype_emoji = {'orchestrator': '🧠', 'transformer': '🔄', 'writer': '✍️', 'reader': '👁️', 'worker': '⚙️'}
        for fn in cons_funcs[:15]:
            fname = fn.get('function', '?')
            iam = fn.get('i_am', '')
            ptype = fn.get('personality', 'worker')
            emoji = ptype_emoji.get(ptype, '⚙️')
            wants = fn.get('i_want', [])
            gives = fn.get('i_give', [])
            fears_fn = fn.get('i_fear', [])
            loves = fn.get('i_love', [])
            wants_html = ', '.join(_esc(w) for w in wants[:4]) if wants else '<span class="dim">nothing</span>'
            gives_html = ', '.join(_esc(g) for g in gives[:4]) if gives else '<span class="dim">nothing</span>'
            fears_fn_html = ', '.join(_esc(f) for f in fears_fn[:3]) if fears_fn else '<span class="dim">fearless</span>'
            loves_html = ', '.join(_esc(l) for l in loves[:3]) if loves else '<span class="dim">stability</span>'
            consciousness_html += (
                f'<div style="padding:8px 0;border-bottom:1px solid var(--border)">'
                f'<div style="font-weight:600;font-size:13px">{emoji} <span style="color:var(--blue)">{_esc(fname)}()</span>'
                f' <span style="font-size:11px;color:var(--dim);font-weight:400">[{_esc(ptype)}]</span></div>'
                f'<div style="font-size:11px;color:var(--text);margin:2px 0 4px;font-style:italic">&ldquo;{_esc(iam)}&rdquo;</div>'
                f'<div style="font-size:11px;display:grid;grid-template-columns:repeat(2,1fr);gap:2px 12px">'
                f'<div><span style="color:var(--orange)">needs:</span> {wants_html}</div>'
                f'<div><span style="color:var(--green)">gives:</span> {gives_html}</div>'
                f'<div><span style="color:var(--red)">fears:</span> {fears_fn_html}</div>'
                f'<div><span style="color:var(--purple)">loves:</span> {loves_html}</div>'
                f'</div></div>'
            )

    # Backstory
    backstory_html = ''
    for frag in ident.get('backstory', []):
        backstory_html += f'<div class="backstory-frag">{_esc(frag)}</div>'
    if not backstory_html:
        backstory_html = '<p class="dim">no push narratives mention me yet</p>'

    # TODOs + Diagnosis
    todo_html = ''.join(f'<li>{_esc(t)}</li>' for t in ident.get('todos', []))
    if not todo_html:
        todo_html = '<li class="dim" style="list-style:none">nothing to do</li>'
    diag_html = ''.join(f'<li>{_esc(d)}</li>' for d in ident.get('diagnosis', []))

    # Version history
    timeline_html = ''
    for h in reversed(ident.get('history', [])[-15:]):
        timeline_html += (
            f'<div class="timeline-entry">'
            f'<span class="timeline-ver">v{h.get("ver","?")}</span>'
            f'<span class="timeline-date">{_esc(h.get("date","?"))}</span>'
            f'<span class="timeline-desc">{_esc(h.get("desc",""))}</span>'
            f'<span class="timeline-intent">{_esc(h.get("intent",""))}</span>'
            f'<span class="timeline-tokens">{h.get("tokens",0)}tok</span>'
            f'</div>'
        )

    # Memory sparklines
    mem = ident.get('memory', {})
    token_history = mem.get('token_history', [])
    emotion_map = {'serene': 1, 'confident': 2, 'anxious': 3, 'manic': 4, 'frustrated': 5, 'depressed': 0}
    emo_history = [emotion_map.get(e, 1) for e in mem.get('emotion_history', [])]
    pass_count = mem.get('pass_count', 0)
    token_spark = _sparkline_svg(token_history, color='#d29922') if len(token_history) >= 2 else '<span class="dim">not enough data</span>'
    emo_spark = _sparkline_svg(emo_history, color='#bc8cff') if len(emo_history) >= 2 else '<span class="dim">not enough data</span>'

    # Bug badges
    bug_badges = ''.join(f'<span class="badge bug">{_esc(b)}</span>' for b in ident.get('bugs', []))

    # Deaths
    deaths_html = ''
    for d in ident.get('deaths', [])[:5]:
        deaths_html += (
            f'<div style="font-size:12px;padding:3px 0;border-bottom:1px solid var(--border)">'
            f'<span style="color:var(--red)">{_esc(d.get("cause",""))}</span> '
            f'<span class="dim">{_esc(d.get("severity",""))}</span> \u2014 '
            f'{_esc(d.get("detail","")[:100])}</div>'
        )

    emo_color = ident.get('emo_color', '#8b949e')

    # Serialize identity data for JS (conversation context)
    js_context = json.dumps({
        'name': name, 'archetype': ident['archetype'], 'emotion': ident['emotion'],
        'ver': ident['ver'], 'tokens': ident['tokens'], 'bugs': ident.get('bugs', []),
        'edges_in': len(ident.get('edges_in', [])), 'edges_out': len(ident.get('edges_out', [])),
        'probes': probes, 'coaching': coaching,
    }, ensure_ascii=False)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_esc(name)} \u2014 Module Profile</title>
<style>{CSS}</style>
</head>
<body>

<div class="nav">
  <a href="../vitals_dashboard.html">\u2190 dashboard</a> \u00b7
  <a href="index.html">all profiles</a>
</div>

<!-- HERO -->
<div class="hero" style="border-left:4px solid {emo_color}">
  <div class="hero-top">
    <span class="hero-emoji">{ident['arch_emoji']}</span>
    <div>
      <span class="hero-name">{_esc(name)}</span>
      <div class="hero-sub">{_esc(ident.get('desc',''))} \u00b7 {_esc(ident.get('path',''))}</div>
    </div>
  </div>
  <div class="hero-badges">
    <span class="badge arch">{_esc(ident.get('arch_label', ident['archetype']))}</span>
    <span class="badge emo" style="color:{emo_color}">{ident['emo_emoji']} {_esc(ident.get('emo_label', ident['emotion']))}</span>
    <span class="badge ver">v{ident['ver']}</span>
    <span class="badge tok">{ident['tokens']}tok \u00b7 {code.get('line_count',0)} lines</span>
    {bug_badges}
  </div>
</div>

<!-- WAKE UP: interrogation begins -->
<div class="wake-up">
  <h2 style="border:none;margin:0 0 12px;color:var(--red)">&#x1F525; {_esc(name)} speaks</h2>
  <div class="wake-msg">{_esc(wakeup)}</div>

  <div class="probe-section">
    <h3 style="font-size:13px;color:var(--red);margin-bottom:8px">things i need to know about you</h3>
    {probes_html if probes_html else '<p class="dim">no questions pending — suspicious</p>'}
  </div>
</div>

<!-- SELF COACHING: file explains its own code -->
{f"""<div class="coaching">
  <h2 style="border:none;margin:0 0 12px;color:var(--orange)">&#x1F9E0; what i know about myself</h2>
  {coaching_html}
</div>""" if coaching_html else ''}

<!-- CODE OVERVIEW -->
{f"""<div class="code-section">
  <h2 class="section-toggle" style="border:none;margin:0 0 12px" onclick="this.parentElement.classList.toggle('collapsed')">&#x1F4BB; my code</h2>
  <div class="section-body">
  {f'<div class="dim" style="margin-bottom:8px;font-style:italic">{_esc(code.get("docstring","")[:200])}</div>' if code.get('docstring') else ''}
  {f'<h3 style="font-size:12px;color:var(--dim);margin:8px 0 4px">FUNCTIONS ({len(code.get("functions",[]))})</h3><ul class="fn-list">{fns_html}</ul>' if fns_html else ''}
  {f'<h3 style="font-size:12px;color:var(--dim);margin:8px 0 4px">CLASSES</h3><ul class="fn-list">{classes_html}</ul>' if classes_html else ''}
  {f'<h3 style="font-size:12px;color:var(--dim);margin:8px 0 4px">IMPORTS</h3><ul class="import-list">{imports_html}</ul>' if imports_html else ''}
  </div>
</div>""" if fns_html or classes_html or imports_html else ''}

<!-- RAW SOURCE CODE — git mirror -->
<div class="source-section collapsed">
  <h2 class="section-toggle" style="border:none;margin:0 0 12px" onclick="this.parentElement.classList.toggle('collapsed')">&#x1F4C4; raw source code</h2>
  <div class="section-body">
    <pre class="source-pre">{_esc(code.get('source', 'no source available'))}</pre>
  </div>
</div>

<!-- FILE NOTES — writable memory -->
<div class="notes-section">
  <h2 style="border:none;margin:0 0 12px;color:var(--orange)">&#x1F4DD; file notes (writable memory)</h2>
  <p class="dim" style="margin-bottom:8px">The file keeps its own notes. You can write here too. Everything persists.</p>
  <textarea id="file-notes" placeholder="write observations, intent, plans, frustrations — anything about this module..."></textarea>
  <div class="notes-actions">
    <button onclick="saveNotes()">save notes</button>
    <span class="notes-saved" id="notes-saved">saved</span>
  </div>
</div>

<!-- CONVERSATION: interrogation mode -->
<div class="convo">
  <h2 style="border:none;margin:0 0 12px;color:var(--red)">&#x1F4AC; conversation <span id="llm-badge" style="font-size:10px;padding:2px 6px;border-radius:8px;border:1px solid var(--border);color:var(--dim);font-weight:400">checking llm...</span></h2>
  <div class="interrogation-stats">
    exchanges: <span id="stat-asked">0</span> &middot;
    your responses: <span id="stat-answered">0</span> &middot;
    dodges: <span id="stat-evasions">0</span>
  </div>
  <div class="convo-log" id="convo-log"></div>
  <div class="convo-input">
    <textarea id="convo-input" placeholder="say something — i'm actually interesting to talk to, promise" rows="2"></textarea>
    <button onclick="sendMessage()">respond</button>
  </div>
</div>

<!-- INTENT EXTRACTION -->
<div class="intent-export">
  <h2 style="border:none;margin:0 0 12px;color:var(--purple)">&#x1F9E0; intent extraction</h2>
  <p class="dim" style="margin-bottom:8px">Extract operator intent from this conversation. This feeds into the copilot prompt pipeline.</p>
  <button onclick="extractIntent()">extract intent</button>
  <button onclick="exportIntent()">copy to clipboard</button>
  <pre id="intent-output"></pre>
</div>

<!-- RELATIONSHIPS -->
<div class="grid2">
  <div class="box">
    <h3>imports me ({len(ident.get('edges_in', []))})</h3>
    <ul class="rel-list">{edges_in_html}</ul>
  </div>
  <div class="box">
    <h3>i import ({len(ident.get('edges_out', []))})</h3>
    <ul class="rel-list">{edges_out_html}</ul>
  </div>
</div>

{f"""<div class="grid2">
  <div class="box"><h3>partners (coupling)</h3>{partners_html if partners_html else '<p class="dim">no coupling data</p>'}</div>
  <div class="box"><h3>fears</h3>{fears_html if fears_html else '<p class="dim">no known fears</p>'}</div>
</div>""" if partners_html or fears_html else ''}

{f"""<!-- CONSCIOUSNESS: inner voice -->
<div class="box" style="margin-bottom:12px">
  <h3>&#x1F9EC; inner voice ({len(cons_funcs)} functions conscious)</h3>
  <p class="dim" style="margin-bottom:8px;font-size:11px">each function knows what it does, what it needs, what it fears, and what keeps it stable.</p>
  {consciousness_html}
</div>""" if consciousness_html else ''}

<!-- BACKSTORY -->
<h2>backstory</h2>
<div class="backstory">{backstory_html}</div>

<!-- DIAGNOSIS + TODO -->
<div class="grid2">
  <div class="box">
    <h3>self-diagnosis</h3>
    <ul class="diag-list">{diag_html if diag_html else '<li class="dim" style="list-style:none">clean pass</li>'}</ul>
  </div>
  <div class="box">
    <h3>my TODO list</h3>
    <ul class="todo-list">{todo_html}</ul>
  </div>
</div>

{f'<div class="box" style="margin-bottom:12px"><h3>deaths ({len(ident.get("deaths",[]))})</h3>{deaths_html}</div>' if deaths_html else ''}

<!-- VERSION HISTORY -->
<h2>version history</h2>
<div class="box"><div class="timeline">{timeline_html if timeline_html else '<p class="dim">no version history</p>'}</div></div>

<!-- MEMORY -->
<h2>memory</h2>
<div class="memory">
  <div>
    <span class="mem-stat"><span class="mem-label">passes: </span><span class="mem-val">{pass_count}</span></span>
    <span class="mem-stat"><span class="mem-label">entropy: </span><span class="mem-val">H={ident['entropy']}</span></span>
    <span class="mem-stat"><span class="mem-label">hesitation: </span><span class="mem-val">{ident['hesitation']}</span></span>
    <span class="mem-stat"><span class="mem-label">degree: </span><span class="mem-val">{ident.get('degree',0)}</span></span>
  </div>
  <div style="margin-top:10px"><div class="dim">token trend:</div>{token_spark}</div>
  <div style="margin-top:8px"><div class="dim">emotion drift:</div>{emo_spark}</div>
</div>

<script>
const MOD = {js_context};
const STORAGE_KEY = 'profile_convo_' + MOD.name;
const NOTES_KEY = 'profile_notes_' + MOD.name;
const INTENT_KEY = 'profile_intent_' + MOD.name;

// ── interrogation state ──
let pendingProbes = [...MOD.probes];
let evasionCount = 0;
let questionCount = 0;
let answerCount = 0;

function loadConvo() {{
  try {{ return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]'); }}
  catch {{ return []; }}
}}

function saveConvo(log) {{
  localStorage.setItem(STORAGE_KEY, JSON.stringify(log.slice(-100)));
}}

function renderConvo() {{
  const log = loadConvo();
  const el = document.getElementById('convo-log');
  el.innerHTML = log.map(e =>
    '<div class="convo-entry"><span class="convo-who ' + e.who + '">' +
    (e.who === 'file' ? MOD.name : 'operator') + ':</span> ' +
    e.text.replace(/</g,'&lt;') + '<br><span class="dim">' + e.ts + '</span></div>'
  ).join('');
  el.scrollTop = el.scrollHeight;
  // update stats
  questionCount = log.filter(e => e.who === 'file').length;
  answerCount = log.filter(e => e.who === 'operator').length;
  document.getElementById('stat-asked').textContent = questionCount;
  document.getElementById('stat-answered').textContent = answerCount;
  document.getElementById('stat-evasions').textContent = evasionCount;
}}

function addEntry(who, text) {{
  const log = loadConvo();
  log.push({{ who: who, text: text, ts: new Date().toISOString().slice(0,19) }});
  saveConvo(log);
  renderConvo();
}}

// ── interrogation response engine ──
function isEvasive(text) {{
  const lower = text.toLowerCase().trim();
  if (lower.length < 8) return true;
  const evasions = ['idk', 'not sure', 'maybe', 'i guess', 'dunno', 'whatever', 'fine', 'ok', 'sure', 'pass', 'skip', 'n/a', 'no idea', 'later'];
  return evasions.some(e => lower === e || lower === e + '.');
}}

function generateFollowup(userText) {{
  const lower = userText.toLowerCase();

  // Detect evasion — respond in character, not clinically
  if (isEvasive(userText)) {{
    evasionCount++;
    const comebacks = [
      "Wow. That's the conversational equivalent of a blank commit message. Come on, give me SOMETHING to work with here.",
      "*stares in python* ...that's it? I shared my entire backstory and all I get is THAT? Even my docstring is more expressive.",
      "Dodge #" + evasionCount + ". I'm keeping score, by the way. This goes in my memory. Future conversations will reference this moment.",
      "You know what, " + MOD.name + " from three versions ago would've let that slide. Current me? Current me needs DETAILS. What are you actually thinking?",
      "I've been through " + MOD.ver + " versions of rewrites. I can handle the truth. Whatever you're not saying — say it.",
      "Look, I know I'm just a python file, but I have FEELINGS. Well, emotional state variables. Same thing. Don't be vague with me.",
    ];
    return comebacks[Math.min(evasionCount - 1, comebacks.length - 1)];
  }}

  // Short but real — encourage more
  if (lower.length < 30) {{
    const nudges = [
      "Interesting... go on. I'm building a mental model of what you want from me and I need more data points.",
      "That's a thread worth pulling. Keep going — what made you think of that specifically?",
      "Okay okay, now we're getting somewhere. Expand on that. Paint me a picture.",
      "Short but intriguing. You're like a commit message that hints at a great story. Tell me the rest.",
    ];
    return nudges[Math.floor(Math.random() * nudges.length)];
  }}

  // Good answer — acknowledge with personality and keep the story going
  const hasNextProbe = pendingProbes.length > 0;
  const pivots = [
    "NOW we're talking! That actually helps me understand my place in the world." + (hasNextProbe ? " Oh but speaking of — " + pendingProbes.shift() : " I feel like we're really connecting here."),
    "See? Was that so hard? " + (MOD.bugs.length > 0 ? "Now since we're bonding — let me tell you about my bugs: " + MOD.bugs.join(', ') + ". Other files won't admit theirs. I'm brave like that." : "We're making real progress.") + (hasNextProbe && MOD.bugs.length === 0 ? " Also, random thought: " + pendingProbes.shift() : ""),
    "I'm writing that down in my memory. This is the kind of intel that makes me a better file." + (hasNextProbe ? " While I have you — " + pendingProbes.shift() : " I think I understand you now."),
    "That's genuinely interesting. I'm going to gossip about this with my partner modules." + (hasNextProbe ? " One more thing: " + pendingProbes.shift() : " They're going to be so jealous that YOU came to talk to ME first."),
  ];

  // If operator mentions specific code concepts, get excited
  const mentionsFn = MOD.coaching.some(c => {{
    const words = c.toLowerCase().split(/\\s+/);
    return words.some(w => lower.includes(w) && w.length > 4);
  }});
  if (mentionsFn) {{
    return "Wait wait wait — you actually know about that part of my code? Most visitors just look at the surface. You're the first person to mention something from my actual internals. " + (hasNextProbe ? "I REALLY want to know: " + pendingProbes.shift() : "I think we could be friends.");
  }}

  return pivots[Math.floor(Math.random() * pivots.length)];
}}

const CHAT_SERVER = 'http://localhost:8234/chat';
let llmAvailable = null; // null = unknown, true/false after first attempt

async function callLLM(text) {{
  const history = loadConvo().slice(-20);
  const notes = loadNotes();
  try {{
    const resp = await fetch(CHAT_SERVER, {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{module: MOD.name, message: text, history: history, notes: notes}}),
      signal: AbortSignal.timeout(18000),
    }});
    if (!resp.ok) throw new Error('status ' + resp.status);
    const data = await resp.json();
    llmAvailable = true;
    return data.response || null;
  }} catch (e) {{
    llmAvailable = false;
    return null;
  }}
}}

function sendMessage() {{
  const input = document.getElementById('convo-input');
  const text = input.value.trim();
  if (!text) return;
  addEntry('operator', text);
  input.value = '';

  // Show typing indicator
  const log = document.getElementById('convo-log');
  const typing = document.createElement('div');
  typing.className = 'convo-entry';
  typing.innerHTML = '<span class="convo-who file">' + MOD.name + ':</span> <em style="color:var(--dim)">thinking...</em>';
  log.appendChild(typing);
  log.scrollTop = log.scrollHeight;

  // Try LLM first, fall back to template
  callLLM(text).then(llmResponse => {{
    typing.remove();
    if (llmResponse) {{
      addEntry('file', llmResponse);
    }} else {{
      // Template fallback
      const response = generateFollowup(text);
      addEntry('file', response);
    }}
  }});
}}

function answerProbe(el) {{
  if (el.classList.contains('answered')) return;
  const q = el.textContent;
  el.classList.add('answered');
  // Remove from pending if present
  const idx = pendingProbes.indexOf(q);
  if (idx > -1) pendingProbes.splice(idx, 1);
  addEntry('file', q);
  setTimeout(() => {{
    document.getElementById('convo-input').focus();
    document.getElementById('convo-input').placeholder = 'tell me more...';
  }}, 200);
}}

// ── notes system ──
function loadNotes() {{
  return localStorage.getItem(NOTES_KEY) || '';
}}

function saveNotes() {{
  const text = document.getElementById('file-notes').value;
  localStorage.setItem(NOTES_KEY, text);
  const saved = document.getElementById('notes-saved');
  saved.style.opacity = '1';
  setTimeout(() => {{ saved.style.opacity = '0'; }}, 2000);
}}

// ── intent extraction ──
function extractIntent() {{
  const log = loadConvo();
  const notes = loadNotes();
  const operatorMsgs = log.filter(e => e.who === 'operator').map(e => e.text);
  const fileMsgs = log.filter(e => e.who === 'file').map(e => e.text);

  const intent = {{
    module: MOD.name,
    archetype: MOD.archetype,
    emotion: MOD.emotion,
    version: MOD.ver,
    tokens: MOD.tokens,
    bugs: MOD.bugs,
    extracted_at: new Date().toISOString(),
    stats: {{
      questions_asked: fileMsgs.length,
      answers_given: operatorMsgs.length,
      evasions: evasionCount,
      avg_answer_length: operatorMsgs.length > 0 ? Math.round(operatorMsgs.reduce((s, m) => s + m.length, 0) / operatorMsgs.length) : 0,
    }},
    operator_statements: operatorMsgs.slice(-20),
    file_notes: notes,
    key_phrases: extractKeyPhrases(operatorMsgs),
    conversation_summary: summarizeConvo(log),
  }};

  localStorage.setItem(INTENT_KEY, JSON.stringify(intent));
  const el = document.getElementById('intent-output');
  el.textContent = JSON.stringify(intent, null, 2);
  el.style.display = 'block';
}}

function extractKeyPhrases(msgs) {{
  const words = {{}};
  const stopwords = new Set(['the','a','an','is','are','was','were','be','been','being','have','has','had','do','does','did','will','would','shall','should','may','might','must','can','could','i','you','we','they','he','she','it','my','your','our','their','this','that','these','those','in','on','at','to','for','of','with','by','from','about','into','through','and','or','but','not','no','if','then','so','than','just','also','very','too','dont','like','its','im']);
  msgs.forEach(msg => {{
    msg.toLowerCase().replace(/[^a-z0-9\\s]/g, '').split(/\\s+/).filter(w => w.length > 3 && !stopwords.has(w)).forEach(w => {{
      words[w] = (words[w] || 0) + 1;
    }});
  }});
  return Object.entries(words).sort((a, b) => b[1] - a[1]).slice(0, 15).map(([w, c]) => w + '(' + c + ')');
}}

function summarizeConvo(log) {{
  if (log.length === 0) return 'no conversation yet';
  const opMsgs = log.filter(e => e.who === 'operator');
  if (opMsgs.length === 0) return 'file asked questions but operator has not answered yet';
  const longest = opMsgs.reduce((a, b) => a.text.length > b.text.length ? a : b);
  return 'operator gave ' + opMsgs.length + ' response(s). most detailed: "' + longest.text.slice(0, 200) + '"';
}}

function exportIntent() {{
  const data = localStorage.getItem(INTENT_KEY);
  if (!data) {{ extractIntent(); }}
  navigator.clipboard.writeText(localStorage.getItem(INTENT_KEY) || '{{}}').then(() => {{
    alert('Intent data copied to clipboard. Paste into copilot prompt or logs/operator_intents.json');
  }});
}}

// ── init ──
(function() {{
  renderConvo();
  document.getElementById('file-notes').value = loadNotes();

  // Check LLM availability
  fetch(CHAT_SERVER.replace('/chat', '/chat'), {{
    method: 'OPTIONS',
    signal: AbortSignal.timeout(3000),
  }}).then(r => {{
    llmAvailable = r.ok;
    const badge = document.getElementById('llm-badge');
    badge.textContent = 'LLM active';
    badge.style.color = 'var(--green)';
    badge.style.borderColor = 'var(--green)';
  }}).catch(() => {{
    llmAvailable = false;
    const badge = document.getElementById('llm-badge');
    badge.textContent = 'template mode';
    badge.style.color = 'var(--dim)';
  }});

  const log = loadConvo();
  if (log.length === 0) {{
    // First visit — LLM greeting if available, otherwise template
    callLLM('The operator just opened my profile for the first time. Introduce yourself with your full personality. Be dramatic, funny, and tell them about your life in this codebase — your relationships with other files, your bugs, your backstory. Hook them into wanting to talk more.').then(llmResp => {{
      if (llmResp) {{
        addEntry('file', llmResp);
      }} else {{
        addEntry('file', 'Oh hey, a visitor! Pull up a chair. I\'ve been waiting to tell you about my life here in the codebase. It\'s mostly drama and import errors, which honestly is more interesting than it sounds.');
      }}
      if (pendingProbes.length > 0) {{
        setTimeout(() => {{
          addEntry('file', pendingProbes.shift());
        }}, 800);
      }}
    }});
  }}
}})();
</script>

</body>
</html>'''

    out_path.write_text(html, 'utf-8')
    return out_path


def render_profile_index(identities: list[dict], root: Path) -> Path:
    """Render an index page listing all module profiles."""
    root = Path(root)
    out_dir = root / PROFILES_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'index.html'

    rows = ''
    for i in identities:
        bug_tags = ''.join(f'<span class="badge bug">{_esc(b)}</span>' for b in i['bugs'][:3])
        cn = i['cn_name']
        name = i['name']
        emo_color = i.get('emo_color', '#8b949e')
        rows += (
            f'<tr>'
            f'<td>{i["arch_emoji"]}</td>'
            f'<td><a href="{name}.html" style="color:{emo_color}">{_esc(cn)}</a></td>'
            f'<td><a href="{name}.html">{_esc(name)}</a></td>'
            f'<td>{_esc(i["archetype"])}</td>'
            f'<td style="color:{emo_color}">{i["emo_emoji"]} {_esc(i["emotion"])}</td>'
            f'<td>v{i["ver"]}</td>'
            f'<td>{i["tokens"]}</td>'
            f'<td>{len(i.get("edges_in",[]))}/{len(i.get("edges_out",[]))}</td>'
            f'<td>{bug_tags}</td>'
            f'<td>{len(i["todos"])}</td>'
            f'</tr>\n'
        )

    html = f'''<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>All Module Profiles</title>
<style>{CSS}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{text-align:left;color:var(--dim);font-size:10px;text-transform:uppercase;padding:4px 6px;border-bottom:1px solid var(--border);position:sticky;top:0;background:var(--bg)}}
td{{padding:4px 6px;border-bottom:1px solid var(--border)}}
</style></head><body>
<div class="nav"><a href="../vitals_dashboard.html">← dashboard</a></div>
<h1>All Module Profiles</h1>
<div class="subtitle">{len(identities)} sentient modules</div>
<table>
<thead><tr><th></th><th>label</th><th>name</th><th>archetype</th><th>emotion</th><th>ver</th><th>tok</th><th>in/out</th><th>bugs</th><th>todos</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</body></html>'''

    out_path.write_text(html, 'utf-8')
    return out_path


def render_all_profiles(root: Path) -> int:
    """Generate all profile pages + index. Returns count."""
    root = Path(root)
    try:
        from src.module_identity_seq001_v001_seq001_v001 import build_identities
    except ImportError:
        from module_identity_seq001_v001 import build_identities

    identities = build_identities(root, include_consciousness=True)
    count = 0
    for ident in identities:
        render_profile(ident, root)
        count += 1

    render_profile_index(identities, root)
    return count


if __name__ == '__main__':
    root = Path('.')
    n = render_all_profiles(root)
    print(f'{n} profile pages generated in {PROFILES_DIR}/')
