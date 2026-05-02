"""vitals_renderer_seq001_v001.py — Dual-substrate codebase dashboard.

Two layers:
  1. Data layer — pure CSS bar charts + inline SVG sparklines (zero JS libs)
  2. Narrative layer — module identity profiles with personality, emotion, voice

Reads: logs/codebase_vitals_seq001_v001.jsonl, pigeon_registry.json, file_heat_map.json,
       logs/entropy_map.json. Outputs: build/vitals_dashboard.html.
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──

import json
import ast
import re
from datetime import datetime, timezone
from html import escape
from pathlib import Path

VITALS_LOG = 'logs/codebase_vitals_seq001_v001.jsonl'
OUTPUT = 'build/vitals_dashboard.html'
HARD_CAP = 200
SNAPSHOT_PATH = 'logs/push_snapshot_seq001_v001s/_latest.json'
_SKIP_DIRS = {'.venv', '__pycache__', '.git', 'node_modules', 'build', '.next'}


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


def _load_latest_snapshot(root: Path) -> dict:
    snap = root / SNAPSHOT_PATH
    if not snap.exists():
        return {}
    try:
        return json.loads(snap.read_text('utf-8'))
    except Exception:
        return {}


def _count_lines(path: Path) -> int:
    try:
        return len(path.read_text('utf-8', errors='ignore').splitlines())
    except Exception:
        return 0


def _iter_workspace_py_files(root: Path):
    for file_path in root.glob('*.py'):
        yield file_path
    for rel_dir in ('src', 'pigeon_compiler', 'pigeon_brain', 'streaming_layer', 'client', 'vscode-extension', 'tests'):
        base = root / rel_dir
        if not base.exists():
            continue
        for file_path in base.rglob('*.py'):
            if any(part in _SKIP_DIRS for part in file_path.relative_to(root).parts):
                continue
            yield file_path


def _live_over_cap_stats(root: Path) -> dict:
    over_files = []
    for file_path in _iter_workspace_py_files(root):
        lines = _count_lines(file_path)
        if lines > HARD_CAP:
            over_files.append((str(file_path.relative_to(root)), lines))
    return {
        'over_cap': len(over_files),
        'worst_offenders': sorted(over_files, key=lambda item: -item[1])[:10],
    }


def _live_import_health(root: Path) -> dict:
    broken = 0
    total = 0
    for init in (root / 'src').rglob('__init__.py'):
        if '__pycache__' in str(init):
            continue
        total += 1
        try:
            code = init.read_text('utf-8', errors='ignore')
            if code.strip():
                ast.parse(code)
        except SyntaxError:
            broken += 1
    healthy = total - broken
    pct = round(healthy / total * 100, 1) if total else 100.0
    return {'healthy': healthy, 'broken': broken, 'total': total, 'health_pct': pct}


def _live_entropy_stats(root: Path) -> dict:
    entropy_path = root / 'logs' / 'entropy_map.json'
    if not entropy_path.exists():
        return {'global_avg': 0, 'high_pct': 0, 'shed_count': 0, 'responses': 0}
    try:
        data = json.loads(entropy_path.read_text('utf-8'))
        return {
            'global_avg': round(data.get('global_avg_entropy', 0), 4),
            'high_pct': round(data.get('high_entropy_pct', 0), 1),
            'shed_count': data.get('shed_blocks_found', 0),
            'responses': data.get('total_responses', 0),
        }
    except Exception:
        return {'global_avg': 0, 'high_pct': 0, 'shed_count': 0, 'responses': 0}


def _live_heat_stats(root: Path) -> dict:
    heat_path = root / 'file_heat_map.json'
    if not heat_path.exists():
        return {'modules_tracked': 0, 'avg_hes': 0, 'hot_count': 0}
    try:
        data = json.loads(heat_path.read_text('utf-8'))
    except Exception:
        return {'modules_tracked': 0, 'avg_hes': 0, 'hot_count': 0}
    hes_vals = []
    for info in data.values():
        samples = info.get('samples', [])
        if samples:
            avg = sum(sample.get('hes', 0) for sample in samples) / len(samples)
            hes_vals.append(avg)
    avg_hes = round(sum(hes_vals) / len(hes_vals), 3) if hes_vals else 0
    hot_count = sum(1 for hes in hes_vals if hes > 0.6)
    return {'modules_tracked': len(data), 'avg_hes': avg_hes, 'hot_count': hot_count}


def _compute_health_score(snapshot: dict) -> float:
    try:
        from src.push_snapshot_seq001_v001_seq001_v001.p_pshsd_s012_v001 import _compute_health_score as score_fn
    except Exception:
        try:
            from push_snapshot_seq001_v001.push_snapshot_seq001_v001_health_score_decomposed_seq012_v001 import _compute_health_score as score_fn
        except Exception:
            compliance = snapshot.get('modules', {}).get('compliance_pct', 0)
            total_bugs = snapshot.get('bugs', {}).get('total', 0)
            total_modules = max(snapshot.get('modules', {}).get('total', 1), 1)
            bug_ratio = min(total_bugs / total_modules, 1.0)
            avg_tokens = snapshot.get('file_stats', {}).get('avg_tokens', 500)
            deaths = snapshot.get('deaths', {}).get('total', 0)
            sync = snapshot.get('cycle', {}).get('sync_score', 0)
            probed = snapshot.get('probes', {}).get('modules_probed', 0)
            avg_hes = snapshot.get('heat', {}).get('avg_hesitation', 0)
            score = 50.0 + (compliance / 100) * 25 - bug_ratio * 20
            if avg_tokens <= 500:
                score += 10
            elif avg_tokens <= 2000:
                score += 5
            elif avg_tokens > 5000:
                score -= 5
            score -= min(deaths * 0.5, 5)
            if sync >= 0.5:
                score += 10
            elif sync >= 0.1:
                score += 8
            elif sync >= 0.03:
                score += 5
            elif sync > 0:
                score += 3
            if probed > 10:
                score += 5
            elif probed > 0:
                score += 2
            if avg_hes > 0.6:
                score -= 5
            elif avg_hes > 0.4:
                score -= 2
            return round(max(0, min(100, score)), 1)
    return score_fn(snapshot)


def _append_latest(values: list[float], current: float | int | None) -> list[float]:
    series = list(values)
    if current is None:
        return series
    if not series or series[-1] != current:
        series.append(current)
    return series


def _bug_summary(by_type: dict) -> str:
    label_map = {
        'hardcoded_import': 'hardcoded',
        'over_hard_cap': 'over-cap',
        'high_coupling': 'coupling',
        'dead_export': 'dead export',
        'query_noise': 'query noise',
        'other': 'other',
    }
    items = [(key, value) for key, value in by_type.items() if value]
    if not items:
        return 'no active bug buckets'
    parts = []
    for key, value in sorted(items, key=lambda item: -item[1])[:3]:
        parts.append(f'{value} {label_map.get(key, key.replace("_", " "))}')
    return ' · '.join(parts)


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


def _parse_ts(raw: str | None) -> datetime | None:
    if not raw:
        return None
    txt = raw.strip().replace(' UTC', '').replace(' ', 'T')
    if re.match(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$', txt):
        txt += ':00'
    if txt.endswith('Z'):
        txt = txt[:-1] + '+00:00'
    elif '+' not in txt[10:] and '-' not in txt[10:]:
        txt += '+00:00'
    try:
        return datetime.fromisoformat(txt).astimezone(timezone.utc)
    except Exception:
        return None


def _fmt_age(age_min: float | None) -> str:
    if age_min is None:
        return '—'
    if age_min < 1:
        return '<1m'
    if age_min < 60:
        return f'{age_min:.0f}m'
    hours = age_min / 60
    if hours < 48:
        return f'{hours:.1f}h' if hours < 10 else f'{hours:.0f}h'
    days = hours / 24
    return f'{days:.1f}d'


def _freshness_status(age_min: float | None, max_age_min: float | None) -> str:
    if age_min is None:
        return 'warning'
    if max_age_min is None:
        return 'fresh'
    if age_min > max_age_min:
        return 'stale'
    if age_min > max_age_min * 0.6:
        return 'warning'
    return 'fresh'


def _status_pill(status: str) -> str:
    cls = {
        'fresh': 'status-fresh',
        'warning': 'status-warning',
        'stale': 'status-stale',
        'missing': 'status-missing',
    }.get(status, 'status-warning')
    return f'<span class="status-pill {cls}">{escape(status)}</span>'


def _build_freshness_section(root: Path) -> str:
    now = datetime.now(timezone.utc)
    counts = {'fresh': 0, 'warning': 0, 'stale': 0, 'missing': 0}
    rows: list[str] = []

    def add_row(name: str, rel_path: str, max_age_min: float | None, note: str,
                *, ts: datetime | None = None, exists: bool | None = None, status: str | None = None):
        full = root / rel_path if rel_path else None
        path_exists = full.exists() if full is not None else bool(exists)
        if exists is not None:
            path_exists = exists
        age_min = None if ts is None else max(0.0, (now - ts).total_seconds() / 60)
        if status is None:
            if not path_exists:
                status = 'missing'
            else:
                status = _freshness_status(age_min, max_age_min)
        counts[status] = counts.get(status, 0) + 1
        href = f'../{rel_path}' if rel_path and path_exists else ''
        open_link = f'<a class="endpoint-link" href="{href}">open</a>' if href else '<span class="dim">—</span>'
        limit = _fmt_age(max_age_min) if max_age_min is not None else '—'
        rows.append(
            f'<tr>'
            f'<td>{escape(name)}</td>'
            f'<td class="mono">{escape(rel_path or "virtual")}</td>'
            f'<td>{_status_pill(status)}</td>'
            f'<td class="num">{_fmt_age(age_min)}</td>'
            f'<td class="num">{limit}</td>'
            f'<td>{escape(note)}</td>'
            f'<td>{open_link}</td>'
            f'</tr>'
        )

    monitored = [
        ('Prompt Journal', 'logs/prompt_journal.jsonl', 30, 'operator prompt capture'),
        ('Prompt Telemetry', 'logs/prompt_telemetry_latest.json', 10, 'latest prompt/session telemetry'),
        ('Chat Compositions', 'logs/chat_compositions.jsonl', 30, 'draft keystroke composition stream'),
        ('Edit Pairs', 'logs/edit_pairs.jsonl', 180, 'prompt ↔ file edit links'),
        ('AI Responses', 'logs/ai_responses.jsonl', 60, 'model output log'),
        ('Entropy Map', 'logs/entropy_map.json', 60, 'uncertainty surface'),
        ('File Heat Map', 'file_heat_map.json', 60, 'touch / attention surface'),
        ('Rework Log', 'rework_log.json', 60, 'response quality signal'),
        ('Escalation State', 'logs/escalation_state.json', 60, 'autonomous escalation signal'),
        ('Active Dossier', 'logs/active_dossier.json', 60, 'bug dossier surface'),
        ('Latest Standup', 'logs/standups/latest_standup.json', 24 * 60, 'module standup chain'),
        ('Latest Manifest Audit', 'logs/manifest_audits/latest_manifest.json', 24 * 60, 'forward/backward audit manifest'),
    ]
    for name, rel_path, max_age_min, note in monitored:
        full = root / rel_path
        ts = datetime.fromtimestamp(full.stat().st_mtime, tz=timezone.utc) if full.exists() else None
        add_row(name, rel_path, max_age_min, note, ts=ts)

    cp = root / '.github' / 'copilot-instructions.md'
    if cp.exists():
        text = cp.read_text('utf-8', errors='replace')
        block_specs = [
            ('Current Query Block', 'current-query', 10, r'Enriched (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC', 'prompt enricher'),
            ('Prompt Telemetry Block', 'prompt-telemetry', 10, r'"updated_at":\s*"([^"]+)"', 'prompt journal refresh'),
            ('Task Context Block', 'task-context', 120, r'Auto-injected (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC', 'dynamic prompt injection'),
        ]
        for name, block_key, max_age_min, pattern, note in block_specs:
            block_match = re.search(
                rf'<!-- pigeon:{re.escape(block_key)} -->([\s\S]*?)<!-- /pigeon:{re.escape(block_key)} -->',
                text,
            )
            if not block_match:
                add_row(name, '.github/copilot-instructions.md', max_age_min, f'{note} — missing block', exists=False, status='missing')
                continue
            ts_match = re.search(pattern, block_match.group(1))
            ts = _parse_ts(ts_match.group(1) if ts_match else None)
            add_row(name, '.github/copilot-instructions.md', max_age_min, note, ts=ts, exists=True, status='warning' if ts is None else None)

    state_path = root / 'pigeon_brain' / 'learning_loop_state.json'
    journal_path = root / 'logs' / 'prompt_journal.jsonl'
    if state_path.exists() and journal_path.exists():
        try:
            state = json.loads(state_path.read_text('utf-8'))
            journal_lines = sum(1 for line in journal_path.read_text('utf-8').splitlines() if line.strip())
            processed = int(state.get('last_processed_line', 0))
            queued = max(0, journal_lines - processed)
            ts = _parse_ts(state.get('last_processed_ts') or state.get('updated_at'))
            age_min = None if ts is None else max(0.0, (now - ts).total_seconds() / 60)
            if queued > 20 or (age_min is not None and age_min > 24 * 60):
                status = 'stale'
            elif queued > 5 or (age_min is not None and age_min > 6 * 60):
                status = 'warning'
            else:
                status = 'fresh'
            add_row('Learning Loop', 'pigeon_brain/learning_loop_state.json', 24 * 60, f'{queued} queued journal entries', ts=ts, exists=True, status=status)
        except Exception:
            add_row('Learning Loop', 'pigeon_brain/learning_loop_state.json', 24 * 60, 'could not parse learning loop state', exists=True, status='warning')

    try:
        registry = json.loads((root / 'pigeon_registry.json').read_text('utf-8'))
        heat = json.loads((root / 'file_heat_map.json').read_text('utf-8'))
        entropy = json.loads((root / 'logs' / 'entropy_map.json').read_text('utf-8'))
        coverage_set = set(heat.keys()) | {str(m.get('module')) for m in entropy.get('top_entropy_modules', [])}
        total = len(registry.get('files', []))
        coverage_pct = (len(coverage_set) / total * 100) if total else 0.0
        status = 'stale' if coverage_pct < 10 else 'warning' if coverage_pct < 25 else 'fresh'
        add_row('Signal Coverage', 'pigeon_registry.json', None, f'{len(coverage_set)}/{total} files with live signal coverage ({coverage_pct:.1f}%)', exists=True, status=status)
    except Exception:
        add_row('Signal Coverage', 'pigeon_registry.json', None, 'could not compute registry coverage', exists=True, status='warning')

    summary_cards = f'''
<div class="grid">
  <div class="card"><div class="label">Fresh Endpoints</div><div class="val green">{counts['fresh']}</div><div class="sub">updating within expected windows</div></div>
  <div class="card"><div class="label">Warnings</div><div class="val" style="color:#d29922">{counts['warning']}</div><div class="sub">aging or partially unreadable</div></div>
  <div class="card"><div class="label">Stale / Missing</div><div class="val red">{counts['stale'] + counts['missing']}</div><div class="sub">needs writer refresh or repair</div></div>
  <div class="card"><div class="label">Tracked Endpoints</div><div class="val blue">{sum(counts.values())}</div><div class="sub">all critical data feeds into the brain</div></div>
</div>'''

    return f'''
<h2>Freshness Surface &amp; Data Endpoints</h2>
<p class="dim" style="margin-bottom:12px">All critical write targets feeding the codebase brain — now visible directly in the vitals page.</p>
{summary_cards}
<div class="box" style="margin-bottom:12px">
  <h3>Data Endpoints</h3>
  <table>
    <thead><tr><th>Surface</th><th>Path</th><th>Status</th><th class="num">Age</th><th class="num">Budget</th><th>Notes</th><th>Open</th></tr></thead>
    <tbody>{''.join(rows)}</tbody>
  </table>
</div>'''


def _build_narrative_section(root: Path) -> str:
    """Build the narrative layer — module identity profiles."""
    try:
        from src.module_identity_seq001_v001 import build_identities
    except ImportError:
        try:
            from module_identity_seq001_v001 import build_identities
        except ImportError:
            return '<p class="dim">Module identity engine not available</p>'

    try:
        identities = build_identities(root)
    except Exception as exc:
        return f'<p class="dim">Module identity engine unavailable: {escape(str(exc))}</p>'
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
            # Backstory excerpt — first fragment from push narratives
            backstory_frags = m.get('backstory', [])
            backstory_html = (
                f'<div class="id-backstory">"{backstory_frags[0][:160]}"</div>'
                if backstory_frags else ''
            )
            # Emotion history arc
            emo_history = m.get('memory', {}).get('emotion_history', [])
            emo_arc_html = ''
            if len(emo_history) >= 2:
                pills = ''.join(f'<span class="emo-pill">{e}</span>' for e in emo_history[-5:])
                emo_arc_html = f'<div class="id-emo-arc">{pills}</div>'
            cards.append(f'''<div class="identity-card" style="border-left:3px solid {m['emo_color']}">
  <div class="id-header">
    <span class="id-emoji">{m['arch_emoji']}</span>
    <a href="{profile_link}" class="id-name" style="color:inherit;text-decoration:none" title="open profile">{cn} <span style="color:var(--dim);font-size:12px">/ {m['name']}</span></a>
    <span class="id-meta">v{m['ver']} · {m['tokens']}tok · {rel_count} edges</span>
    <span class="id-emotion" title="{m['emotion']}">{m['emo_emoji']}</span>
  </div>
  <div class="id-voice">"{m['voice']}"</div>
  {backstory_html}
  {emo_arc_html}
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
    snapshot = _load_latest_snapshot(root)
    out_path = root / (output or OUTPUT)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not vitals and not snapshot:
        out_path.write_text('<h1>No vitals data yet</h1>', 'utf-8')
        return out_path

    latest_vitals = vitals[-1] if vitals else {}
    live_over_cap = _live_over_cap_stats(root)
    live_imports = _live_import_health(root)
    live_entropy = _live_entropy_stats(root)
    live_heat = _live_heat_stats(root)

    if snapshot:
        latest_commit = snapshot.get('commit', '?')[:8]
        latest_msg = snapshot.get('commit_msg') or snapshot.get('intent', '')
        latest_ts = snapshot.get('ts', '')
        lc = {
            'compliant': snapshot.get('modules', {}).get('compliant', 0),
            'over_cap': snapshot.get('modules', {}).get('over_cap', 0),
            'total': snapshot.get('modules', {}).get('total', 0),
            'compliance_pct': snapshot.get('modules', {}).get('compliance_pct', 0),
        }
        bug_types = {
            key: value for key, value in snapshot.get('bugs', {}).items()
            if key != 'total' and value
        }
        lb = {
            'total': snapshot.get('bugs', {}).get('total', 0),
            'by_type': bug_types,
        }
        tracked_modules = snapshot.get('modules', {}).get('total', 0)
        avg_tokens = snapshot.get('file_stats', {}).get('avg_tokens', 0)
        files_over_200 = snapshot.get('file_stats', {}).get('files_over_200', 0)
        health_score = _compute_health_score(snapshot)
    else:
        latest_commit = latest_vitals.get('commit', '?')
        latest_msg = latest_vitals.get('commit_msg', '')
        latest_ts = latest_vitals.get('ts', '')
        lc = latest_vitals.get('compliance', {})
        lb = latest_vitals.get('bugs', {})
        tracked_modules = latest_vitals.get('files', {}).get('total', 0)
        avg_tokens = 0
        files_over_200 = lc.get('over_cap', 0)
        health_score = 0

    li = live_imports if live_imports.get('total', 0) else latest_vitals.get('imports', {})
    le = live_entropy if (live_entropy.get('responses', 0) or live_entropy.get('global_avg', 0)) else latest_vitals.get('entropy', {})
    lh = live_heat if live_heat.get('modules_tracked', 0) else latest_vitals.get('heat', {})

    # Time series extraction
    compliance_ts = _append_latest([v.get('compliance', {}).get('compliance_pct', 0) for v in vitals], lc.get('compliance_pct', 0))
    import_ts = _append_latest([v.get('imports', {}).get('health_pct', 0) for v in vitals], li.get('health_pct', 0))
    entropy_ts = _append_latest([v.get('entropy', {}).get('global_avg', 0) for v in vitals], le.get('global_avg', 0))
    bug_ts = _append_latest([v.get('bugs', {}).get('total', 0) for v in vitals], lb.get('total', 0))
    file_ts = _append_latest([v.get('files', {}).get('total', 0) for v in vitals], tracked_modules)
    over_cap_ts = _append_latest([v.get('compliance', {}).get('over_cap', 0) for v in vitals], lc.get('over_cap', 0))

    worst = live_over_cap.get('worst_offenders', [])
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

    # Freshness + narrative layers
    freshness_html = _build_freshness_section(root)
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
.id-backstory{{font-size:11px;color:var(--dim);padding-left:28px;margin:2px 0 4px;border-left:2px solid var(--border);margin-left:28px;padding-left:8px}}
.id-emo-arc{{display:flex;gap:4px;align-items:center;padding-left:28px;margin-bottom:4px;flex-wrap:wrap}}
.emo-pill{{font-size:9px;padding:1px 5px;border-radius:8px;border:1px solid var(--border);color:var(--dim)}}
.id-tags{{display:flex;flex-wrap:wrap;gap:4px;padding-left:28px}}
.tag{{font-size:10px;padding:1px 6px;border-radius:10px;border:1px solid var(--border)}}
.tag.arch{{color:var(--blue)}}
.tag.emo{{color:var(--purple)}}
.tag.hes{{color:var(--orange)}}
.tag.ent{{color:var(--orange)}}
.tag.bug{{color:var(--red)}}
.id-desc{{color:var(--dim);font-size:11px;padding-left:28px;margin-top:4px}}
.identity-grid{{display:grid;grid-template-columns:1fr 1fr;gap:8px}}
.status-pill{{display:inline-block;padding:2px 8px;border-radius:999px;font-size:10px;text-transform:uppercase;border:1px solid var(--border)}}
.status-fresh{{color:var(--green)}}
.status-warning{{color:var(--orange)}}
.status-stale,.status-missing{{color:var(--red)}}
.endpoint-link{{color:var(--blue);text-decoration:none}}
.endpoint-link:hover{{text-decoration:underline}}

@media(max-width:800px){{.row2,.identity-grid{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<h1>Codebase Brain Stats</h1>
<div class="subtitle">
    {len(vitals)} snapshots &middot; latest: {latest_commit}
    {(' &mdash; ' + str(latest_msg)[:60]) if latest_msg else ''}
    &middot; {_fmt_ts(latest_ts)}
</div>

<!-- ═══ DATA LAYER ═══ -->
<h2>Vital Signs</h2>
<div class="grid">
    <div class="card">
        <div class="label">Health Score</div>
        <div class="val" style="color:{_pct_color(health_score)}">{health_score}/100</div>
        <div class="sub">latest push snapshot composite</div>
    </div>
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
        <div class="sub">{_bug_summary(bug_types)}</div>
    <div class="spark">{spk_bugs}</div>
  </div>
  <div class="card">
    <div class="label">Cognitive Heat</div>
    <div class="val" style="color:{_color_for(lh.get('hot_count',0),(3,8))}">{lh.get('hot_count',0)}</div>
    <div class="sub">modules w/ hesitation &gt;0.6 &middot; avg={lh.get('avg_hes',0)}</div>
  </div>
  <div class="card">
        <div class="label">Tracked Modules</div>
        <div class="val blue">{tracked_modules}</div>
        <div class="sub">{lc.get('over_cap',0)} over-cap modules &middot; {files_over_200} files &gt;200 lines &middot; avg {avg_tokens:.0f} tok</div>
    <div class="spark">{spk_files}</div>
  </div>
</div>

{freshness_html}

<div class="row2">
  <div class="box">
        <h3>Longest Live Python Files ({live_over_cap.get('over_cap',0)} files &gt; {HARD_CAP} lines)</h3>
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

