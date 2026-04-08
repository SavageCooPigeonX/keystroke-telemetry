"""vitals_renderer.py — Dual-substrate codebase dashboard.

Two layers:
  1. Data layer — pure CSS bar charts + inline SVG sparklines (zero JS libs)
  2. Narrative layer — module identity profiles with personality, emotion, voice

Reads: logs/codebase_vitals.jsonl, pigeon_registry.json, file_heat_map.json,
       logs/entropy_map.json. Outputs: build/vitals_dashboard.html.
"""
# ── telemetry:pulse ──
# EDIT_TS:   2026-04-06T03:10:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  add chinese names profile links todos
# EDIT_AUTHOR: copilot
# EDIT_STATE: harvested
# ── /pulse ──

import json
from datetime import datetime
from pathlib import Path

VITALS_LOG = 'logs/codebase_vitals.jsonl'
OUTPUT = 'build/vitals_dashboard.html'
HARD_CAP = 200


def _load_vitals(root: Path) -> list[dict]:
    log = root / VITALS_LOG
    if not log.exists():
        return []
    entries = []
    for line in log.read_text('utf-8').splitlines():
        if line.strip():
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def _fmt_ts(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso)
        return dt.strftime('%m/%d %H:%M')
    except Exception:
        return iso[:16]


def _sparkline_svg(values: list[float], w: int = 120, h: int = 28,
                   color: str = '#58a6ff') -> str:
    """Generate an inline SVG sparkline from a list of values. Pure SVG, no JS."""
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


def _bar_css(value: float, max_val: float, color: str = '#3fb950') -> str:
    """Generate a CSS bar for a value."""
    pct = min(100, (value / max_val * 100)) if max_val else 0
    return (f'<div style="background:{color};height:6px;border-radius:3px;'
            f'width:{pct:.1f}%;min-width:2px"></div>')


def _color_for(val: float, thresholds: tuple = (0.3, 0.6)) -> str:
    lo, hi = thresholds
    if val <= lo:
        return '#3fb950'
    if val <= hi:
        return '#d29922'
    return '#f85149'


def _pct_color(pct: float) -> str:
    if pct >= 90:
        return '#3fb950'
    if pct >= 70:
        return '#d29922'
    return '#f85149'


def _build_narrative_section(root: Path) -> str:
    """Build the narrative layer — module identity profiles."""
    try:
        from src.module_identity import build_identities
    except ImportError:
        try:
            from module_identity import build_identities
        except ImportError:
            return '<p class="dim">Module identity engine not available</p>'

    identities = build_identities(root)
    if not identities:
        return '<p class="dim">No module identities found</p>'

    # Group by archetype for narrative structure
    groups = {}
    for ident in identities:
        arch = ident['archetype']
        groups.setdefault(arch, []).append(ident)

    # Priority order for display
    priority = ['bloated', 'hothead', 'frustrated', 'orphan',
                'veteran', 'anchor', 'healer', 'rookie', 'stable']

    cards = []
    shown = 0
    for arch in priority:
        if arch not in groups:
            continue
        mods = groups[arch][:6]  # Cap per group
        for m in mods:
            if shown >= 24:
                break
            bug_tags = ''.join(
                f'<span class="tag bug">{b}</span>' for b in m['bugs'][:3]
            )
            cn = m.get('cn_name', m['name'])
            profile_link = f'profiles/{m["name"]}.html'
            todo_count = len(m.get('todos', []))
            rel_count = len(m.get('edges_in', [])) + len(m.get('edges_out', []))
            cards.append(f'''<div class="identity-card" style="border-left:3px solid {m['emo_color']}">
  <div class="id-header">
    <span class="id-emoji">{m['arch_emoji']}</span>
    <a href="{profile_link}" class="id-name" style="color:inherit;text-decoration:none" title="open profile">{cn} <span style="color:var(--dim);font-size:12px">/ {m['name']}</span></a>
    <span class="id-meta">v{m['ver']} · {m['tokens']}tok · {rel_count} edges</span>
    <span class="id-emotion" title="{m['emotion']}">{m['emo_emoji']}</span>
  </div>
  <div class="id-voice">"{m['voice']}"</div>
  <div class="id-tags">
    <span class="tag arch">{m['archetype']}</span>
    <span class="tag emo">{m['emotion']}</span>
    {f'<span class="tag hes">hes={m["hesitation"]}</span>' if m['hesitation'] > 0 else ''}
    {f'<span class="tag ent">H={m["entropy"]}</span>' if m['entropy'] > 0 else ''}
    {f'<span class="tag" style="color:var(--orange)">todos:{todo_count}</span>' if todo_count else ''}
    {bug_tags}
  </div>
  {f'<div class="id-desc">{m["desc"]}</div>' if m['desc'] else ''}
</div>''')
            shown += 1

    remaining = len(identities) - shown
    footer = (f'<div class="dim" style="text-align:center;padding:12px">'
              f'<a href="profiles/index.html">+{remaining} more modules → all profiles</a>'
              f'</div>' if remaining > 0 else '')

    return '\n'.join(cards) + footer


def render_dashboard(root: Path, output: str | None = None) -> Path:
    """Generate the dual-substrate vitals dashboard."""
    root = Path(root)
    vitals = _load_vitals(root)
    out_path = root / (output or OUTPUT)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not vitals:
        out_path.write_text('<h1>No vitals data yet</h1>', 'utf-8')
        return out_path

    latest = vitals[-1]

    # Time series extraction
    compliance_ts = [v.get('compliance', {}).get('compliance_pct', 0) for v in vitals]
    import_ts = [v.get('imports', {}).get('health_pct', 0) for v in vitals]
    entropy_ts = [v.get('entropy', {}).get('global_avg', 0) for v in vitals]
    bug_ts = [v.get('bugs', {}).get('total', 0) for v in vitals]
    file_ts = [v.get('files', {}).get('total', 0) for v in vitals]
    over_cap_ts = [v.get('compliance', {}).get('over_cap', 0) for v in vitals]

    # Latest values
    lc = latest.get('compliance', {})
    lb = latest.get('bugs', {})
    le = latest.get('entropy', {})
    li = latest.get('imports', {})
    lh = latest.get('heat', {})
    lf = latest.get('files', {})

    worst = lc.get('worst_offenders', [])
    worst_rows = '\n'.join(
        f'<tr><td class="mono">{f}</td>'
        f'<td class="num">{n}</td>'
        f'<td>{_bar_css(n, 1500, "#f85149")}</td></tr>'
        for f, n in worst[:8]
    )

    # Bug breakdown
    bug_types = lb.get('by_type', {})
    bug_rows = '\n'.join(
        f'<tr><td>{t}</td><td class="num">{c}</td></tr>'
        for t, c in sorted(bug_types.items(), key=lambda x: -x[1])[:5]
    )

    # Sparklines
    spk_compliance = _sparkline_svg(compliance_ts, color='#3fb950')
    spk_entropy = _sparkline_svg(entropy_ts, color='#d29922')
    spk_bugs = _sparkline_svg(bug_ts, color='#f85149')
    spk_files = _sparkline_svg(file_ts, color='#58a6ff')
    spk_overcap = _sparkline_svg(over_cap_ts, color='#f85149')
    spk_imports = _sparkline_svg(import_ts, color='#58a6ff')

    # Narrative layer
    narrative_html = _build_narrative_section(root)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Codebase Brain Stats</title>
<style>
:root {{
  --bg:#0d1117;--card:#161b22;--border:#30363d;
  --text:#c9d1d9;--dim:#8b949e;--green:#3fb950;
  --orange:#d29922;--red:#f85149;--blue:#58a6ff;--purple:#bc8cff;
}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;background:var(--bg);color:var(--text);padding:20px;max-width:1200px;margin:0 auto}}
h1{{font-size:22px;margin-bottom:2px}}
h2{{font-size:16px;color:var(--dim);margin:24px 0 12px;border-bottom:1px solid var(--border);padding-bottom:6px}}
.subtitle{{color:var(--dim);font-size:12px;margin-bottom:16px}}
.dim{{color:var(--dim);font-size:12px}}

/* Stat cards */
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px;margin-bottom:16px}}
.card{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px}}
.card .label{{color:var(--dim);font-size:10px;text-transform:uppercase;letter-spacing:.5px}}
.card .val{{font-size:26px;font-weight:600;margin:2px 0}}
.card .sub{{color:var(--dim);font-size:11px;margin-top:2px}}
.card .spark{{margin-top:6px}}

/* Colors */
.green{{color:var(--green)}}.orange{{color:var(--orange)}}.red{{color:var(--red)}}.blue{{color:var(--blue)}}

/* Tables */
table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{text-align:left;color:var(--dim);font-size:10px;text-transform:uppercase;padding:4px 6px;border-bottom:1px solid var(--border)}}
td{{padding:4px 6px;border-bottom:1px solid var(--border)}}
.mono{{font-family:'Cascadia Code','Fira Code',monospace;font-size:11px}}
.num{{text-align:right;font-variant-numeric:tabular-nums}}

/* Two-col layout */
.row2{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}}
.box{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px}}
.box h3{{font-size:13px;color:var(--dim);margin-bottom:8px}}

/* Identity cards */
.identity-card{{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:12px;margin-bottom:8px}}
.id-header{{display:flex;align-items:center;gap:8px}}
.id-emoji{{font-size:18px}}
.id-name{{font-weight:600;font-size:14px}}
.id-meta{{color:var(--dim);font-size:11px;margin-left:auto}}
.id-emotion{{font-size:16px}}
.id-voice{{font-style:italic;color:var(--text);font-size:12px;margin:6px 0 4px;padding-left:28px;opacity:0.85}}
.id-tags{{display:flex;flex-wrap:wrap;gap:4px;padding-left:28px}}
.tag{{font-size:10px;padding:1px 6px;border-radius:10px;border:1px solid var(--border)}}
.tag.arch{{color:var(--blue)}}
.tag.emo{{color:var(--purple)}}
.tag.hes{{color:var(--orange)}}
.tag.ent{{color:var(--orange)}}
.tag.bug{{color:var(--red)}}
.id-desc{{color:var(--dim);font-size:11px;padding-left:28px;margin-top:4px}}
.identity-grid{{display:grid;grid-template-columns:1fr 1fr;gap:8px}}

@media(max-width:800px){{.row2,.identity-grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<h1>Codebase Brain Stats</h1>
<div class="subtitle">
  {len(vitals)} snapshots &middot; latest: {latest.get('commit','?')}
  {(' &mdash; ' + latest.get('commit_msg','')[:60]) if latest.get('commit_msg') else ''}
  &middot; {_fmt_ts(latest.get('ts',''))}
</div>

<!-- ═══ DATA LAYER ═══ -->
<h2>Vital Signs</h2>
<div class="grid">
  <div class="card">
    <div class="label">Compliance</div>
    <div class="val" style="color:{_pct_color(lc.get('compliance_pct',0))}">{lc.get('compliance_pct',0)}%</div>
    <div class="sub">{lc.get('compliant',0)}/{lc.get('total',0)} under {HARD_CAP}-line cap</div>
    <div class="spark">{spk_compliance}</div>
  </div>
  <div class="card">
    <div class="label">Import Health</div>
    <div class="val" style="color:{_pct_color(li.get('health_pct',0))}">{li.get('health_pct',0)}%</div>
    <div class="sub">{li.get('healthy',0)}/{li.get('total',0)} clean __init__.py</div>
    <div class="spark">{spk_imports}</div>
  </div>
  <div class="card">
    <div class="label">Entropy</div>
    <div class="val" style="color:{_color_for(le.get('global_avg',0),(0.25,0.35))}">H={le.get('global_avg',0)}</div>
    <div class="sub">{le.get('high_pct',0)}% high &middot; {le.get('shed_count',0)} sheds</div>
    <div class="spark">{spk_entropy}</div>
  </div>
  <div class="card">
    <div class="label">Bugs</div>
    <div class="val" style="color:{_color_for(lb.get('total',0),(10,50))}">{lb.get('total',0)}</div>
    <div class="sub">{lb.get('critical',0)} critical</div>
    <div class="spark">{spk_bugs}</div>
  </div>
  <div class="card">
    <div class="label">Cognitive Heat</div>
    <div class="val" style="color:{_color_for(lh.get('hot_count',0),(3,8))}">{lh.get('hot_count',0)}</div>
    <div class="sub">modules w/ hesitation &gt;0.6 &middot; avg={lh.get('avg_hes',0)}</div>
  </div>
  <div class="card">
    <div class="label">Total Files</div>
    <div class="val blue">{lf.get('total',0)}</div>
    <div class="sub">src:{lf.get('src',0)} compiler:{lf.get('pigeon_compiler',0)} brain:{lf.get('pigeon_brain',0)}</div>
    <div class="spark">{spk_files}</div>
  </div>
</div>

<div class="row2">
  <div class="box">
    <h3>Over-Cap Offenders ({lc.get('over_cap',0)} files)</h3>
    <table>
      <thead><tr><th>File</th><th class="num">Lines</th><th style="width:40%">Severity</th></tr></thead>
      <tbody>{worst_rows if worst_rows else '<tr><td colspan="3">All compliant</td></tr>'}</tbody>
    </table>
    <div class="spark" style="margin-top:8px">
      <span class="dim">over-cap trend:</span> {spk_overcap}
    </div>
  </div>
  <div class="box">
    <h3>Bug Breakdown</h3>
    <table>
      <thead><tr><th>Type</th><th class="num">Count</th></tr></thead>
      <tbody>{bug_rows if bug_rows else '<tr><td colspan="2">No bugs</td></tr>'}</tbody>
    </table>
    <div class="spark" style="margin-top:8px">
      <span class="dim">bug trend:</span> {spk_bugs}
    </div>
  </div>
</div>

<!-- ═══ NARRATIVE LAYER ═══ -->
<h2>Module Identities</h2>
<p class="dim" style="margin-bottom:12px">
  Each module has a personality derived from its behavior — churn, entropy, bugs, cognitive heat.
  They speak. Screenshot this for copilot context.
</p>
<div class="identity-grid">
{narrative_html}
</div>

</body>
</html>'''

    out_path.write_text(html, 'utf-8')
    return out_path


if __name__ == '__main__':
    root = Path('.')
    out = render_dashboard(root)
    print(f"Dashboard: {out}")

