"""Intent simulator — runs ahead of operator, hallucinating their future.

Reads development timelines, prompt patterns, cognitive load, deleted words,
and push velocity to simulate operator intent 1 week / 1 month / 3 months out.
Merges with operator coaching as a per-push project management layer.
Adapts intent quickly based on recent prompts. Zero LLM calls.
"""


from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from statistics import mean, stdev


# ── §0 data loaders ──────────────────────────

def _git_log(root: Path, days: int = 30) -> list[dict]:
    """Parse git log into structured records."""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime('%Y-%m-%d')
    try:
        result = subprocess.run(
            ['git', 'log', f'--since={since}', '--pretty=format:%H|%aI|%s', '--no-merges'],
            cwd=str(root), capture_output=True, text=True, timeout=10
        )
        commits = []
        for line in result.stdout.strip().splitlines():
            parts = line.split('|', 2)
            if len(parts) == 3:
                commits.append({
                    'hash': parts[0][:8],
                    'ts': parts[1],
                    'msg': parts[2],
                })
        return commits
    except Exception:
        return []


def _load_journal(root: Path, n: int = 100) -> list[dict]:
    """Load recent prompt journal entries."""
    path = root / 'logs' / 'prompt_journal.jsonl'
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding='utf-8').strip().splitlines()
        entries = []
        for line in lines[-n:]:
            try:
                entries.append(json.loads(line))
            except Exception:
                pass
        return entries
    except Exception:
        return []


def _load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return None


# ── §1 timeline analysis ─────────────────────

def _analyze_velocity(commits: list[dict]) -> dict:
    """Compute development velocity and acceleration."""
    if len(commits) < 2:
        return {'commits_per_day': 0, 'acceleration': 0, 'active_days': 0}

    # parse timestamps
    dates = []
    for c in commits:
        try:
            dt = datetime.fromisoformat(c['ts'])
            dates.append(dt)
        except Exception:
            pass

    if len(dates) < 2:
        return {'commits_per_day': 0, 'acceleration': 0, 'active_days': 0}

    dates.sort()
    span = (dates[-1] - dates[0]).total_seconds() / 86400 or 1
    cpd = len(dates) / span

    # acceleration: compare first half vs second half velocity
    mid = len(dates) // 2
    first_span = (dates[mid] - dates[0]).total_seconds() / 86400 or 1
    second_span = (dates[-1] - dates[mid]).total_seconds() / 86400 or 1
    first_vel = mid / first_span
    second_vel = (len(dates) - mid) / second_span
    accel = (second_vel - first_vel) / first_vel if first_vel else 0

    # unique active days
    active_days = len({d.date() for d in dates})

    return {
        'commits_per_day': round(cpd, 1),
        'acceleration': round(accel, 2),
        'active_days': active_days,
        'first_half_vel': round(first_vel, 1),
        'second_half_vel': round(second_vel, 1),
    }


def _extract_intent_signals(commits: list[dict]) -> list[dict]:
    """Extract intent categories from commit messages."""
    categories = {
        'compression': ['compress', 'glyph', 'symbol', 'token', 'dictionary'],
        'self_heal': ['heal', 'self-fix', 'self_fix', 'rename', 'import'],
        'telemetry': ['telemetry', 'keystroke', 'cognitive', 'operator'],
        'prediction': ['predict', 'forecast', 'scorer', 'confidence'],
        'infrastructure': ['pigeon', 'compiler', 'manifest', 'registry'],
        'research': ['research', 'lab', 'narrative', 'story'],
        'product': ['readme', 'release', 'market', 'gtm'],
        'flow_engine': ['flow', 'electron', 'backward', 'node', 'loop'],
    }

    signals = []
    for c in commits:
        msg = c['msg'].lower()
        matched = []
        for cat, keywords in categories.items():
            if any(k in msg for k in keywords):
                matched.append(cat)
        signals.append({**c, 'intents': matched or ['unclassified']})
    return signals


def _compute_intent_trajectory(signals: list[dict]) -> dict:
    """Where is development heading based on commit history."""
    if not signals:
        return {'dominant': 'unknown', 'emerging': [], 'declining': [], 'timeline': {}}

    # split into halves for trend
    mid = len(signals) // 2 or 1
    first_half = signals[:mid]
    second_half = signals[mid:]

    first_counts = Counter()
    for s in first_half:
        for i in s['intents']:
            first_counts[i] += 1

    second_counts = Counter()
    for s in second_half:
        for i in s['intents']:
            second_counts[i] += 1

    all_cats = set(first_counts) | set(second_counts)
    trends = {}
    for cat in all_cats:
        f_norm = first_counts[cat] / len(first_half) if first_half else 0
        s_norm = second_counts[cat] / len(second_half) if second_half else 0
        trends[cat] = round(s_norm - f_norm, 3)

    emerging = sorted([c for c, d in trends.items() if d > 0.05], key=lambda c: trends[c], reverse=True)
    declining = sorted([c for c, d in trends.items() if d < -0.05], key=lambda c: trends[c])
    dominant = second_counts.most_common(1)[0][0] if second_counts else 'unknown'

    return {
        'dominant': dominant,
        'emerging': emerging[:3],
        'declining': declining[:3],
        'trends': trends,
    }


# ── §2 prompt pattern analysis ────────────────

def _analyze_prompt_patterns(entries: list[dict]) -> dict:
    """Extract intent patterns from prompt journal."""
    if not entries:
        return {}

    # intent distribution
    intents = Counter(e.get('intent', 'unknown') for e in entries)

    # module focus from hot_modules + module_refs
    module_mentions = Counter()
    for e in entries:
        for ref in e.get('module_refs', []):
            module_mentions[ref] += 1
        for hm in e.get('hot_modules', []):
            m = hm.get('module', '')
            if m:
                module_mentions[m] += 1

    # deleted word themes — what operator almost asked
    # extract individual words from deleted fragments (short, meaningful tokens)
    deleted = []
    for e in entries:
        for dw in e.get('deleted_words', []):
            w = dw if isinstance(dw, str) else dw.get('text', str(dw))
            w = w.strip().lower()
            # split long fragments into words, keep short ones whole
            if len(w) > 30:
                for word in w.split():
                    word = re.sub(r'[^a-z]', '', word)
                    if 3 <= len(word) <= 20:
                        deleted.append(word)
            elif 2 < len(w) <= 30:
                deleted.append(w)

    # cognitive state trajectory
    states = [e.get('cognitive_state', 'unknown') for e in entries[-20:]]
    state_counts = Counter(states)

    # avg deletion ratio trend
    del_ratios = [e.get('deletion_ratio', 0) or 0 for e in entries if e.get('deletion_ratio') is not None]

    return {
        'intent_distribution': dict(intents.most_common(5)),
        'module_focus': dict(module_mentions.most_common(10)),
        'deleted_themes': deleted[-20:],
        'cognitive_trend': dict(state_counts),
        'avg_deletion': round(mean(del_ratios), 3) if del_ratios else 0,
    }


# ── §3 forward projection ────────────────────

def _project_forward(velocity: dict, trajectory: dict, patterns: dict) -> dict:
    """Simulate operator intent at 1 week / 1 month / 3 months."""
    cpd = velocity.get('commits_per_day', 0)
    accel = velocity.get('acceleration', 0)
    dominant = trajectory.get('dominant', 'unknown')
    emerging = trajectory.get('emerging', [])
    declining = trajectory.get('declining', [])
    module_focus = patterns.get('module_focus', {})
    deleted_themes = patterns.get('deleted_themes', [])

    # 1 week: extrapolate current dominant + acceleration
    week_commits = round(cpd * 7 * (1 + accel * 0.5))
    week_focus = dominant
    week_secondary = emerging[0] if emerging else None

    # 1 month: emerging intents overtake if acceleration holds
    month_commits = round(cpd * 30 * (1 + accel))
    month_focus = emerging[0] if emerging and accel > 0.1 else dominant
    month_risk = declining[0] if declining else None

    # 3 months: deleted themes resurface — what they almost asked IS what they'll build
    three_month_themes = list(set(deleted_themes))[:5] if deleted_themes else []
    three_month_focus = 'product' if 'market' in ' '.join(deleted_themes) or 'release' in ' '.join(deleted_themes) else month_focus

    # module prediction: top modules extrapolated forward
    top_modules = sorted(module_focus.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        'week': {
            'estimated_commits': week_commits,
            'primary_intent': week_focus,
            'secondary_intent': week_secondary,
            'confidence': 'high' if cpd > 2 else 'medium' if cpd > 0.5 else 'low',
        },
        'month': {
            'estimated_commits': month_commits,
            'primary_intent': month_focus,
            'abandoned_risk': month_risk,
            'confidence': 'medium' if cpd > 1 else 'low',
        },
        'quarter': {
            'emerging_themes': three_month_themes,
            'primary_intent': three_month_focus,
            'module_prediction': [m for m, _ in top_modules],
            'confidence': 'speculative',
        },
    }


# ── §4 coaching synthesis ─────────────────────

def _synthesize_coaching(projection: dict, patterns: dict, velocity: dict) -> list[str]:
    """Generate project management directives from the projection."""
    directives = []

    week = projection.get('week', {})
    month = projection.get('month', {})
    quarter = projection.get('quarter', {})

    # velocity-based
    accel = velocity.get('acceleration', 0)
    if accel > 0.3:
        directives.append(
            f'Development accelerating ({accel:+.0%}) — operator is in build mode. '
            'Minimize friction: provide complete code, skip explanations unless asked.'
        )
    elif accel < -0.3:
        directives.append(
            f'Development decelerating ({accel:+.0%}) — operator may be blocked or shifting focus. '
            'Offer architecture-level suggestions, not just code.'
        )

    # intent shift detection
    if week.get('secondary_intent') and week['secondary_intent'] != week.get('primary_intent'):
        directives.append(
            f'Intent bifurcation: `{week["primary_intent"]}` dominant but `{week["secondary_intent"]}` emerging — '
            'watch for context switches mid-session.'
        )

    # abandoned risk
    if month.get('abandoned_risk'):
        directives.append(
            f'`{month["abandoned_risk"]}` declining — operator may have deprioritized this. '
            'Don\'t suggest work in this area unless explicitly asked.'
        )

    # deleted themes as future intent
    themes = quarter.get('emerging_themes', [])
    if themes:
        top3 = ', '.join(f'`{t}`' for t in themes[:3])
        directives.append(
            f'Unsaid themes detected: {top3} — these are words deleted from prompts. '
            'Operator is thinking about these but hasn\'t committed. Explore when relevant.'
        )

    # cognitive load
    avg_del = patterns.get('avg_deletion', 0)
    if avg_del > 0.3:
        directives.append(
            f'High restructuring ({avg_del:.0%} deletion avg) — operator rewrites heavily before asking. '
            'Provide structured, modular responses they can adapt without full rewrites.'
        )

    # module focus stickiness
    modules = patterns.get('module_focus', {})
    if modules:
        top = list(modules.keys())[:3]
        directives.append(
            f'Module focus cluster: {", ".join(f"`{m}`" for m in top)} — '
            'pre-load context from these modules when operator starts typing.'
        )

    return directives


# ── §5 report generator ──────────────────────

def _format_report(velocity: dict, trajectory: dict, patterns: dict,
                    projection: dict, coaching: list[str], commits: list[dict]) -> str:
    """Format the intent simulation as a prediction report."""
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = [
        '# Intent Simulation Report',
        '',
        f'*Auto-generated {now} · {len(commits)} commits analyzed · zero LLM calls*',
        '',
        '> This is a forward projection of operator intent based on development timeline, prompt patterns,',
        '> deleted words, and cognitive load signals. Predictions become pass/fail on next push.',
        '',
    ]

    # velocity
    lines.append('## Development Velocity\n')
    cpd = velocity.get('commits_per_day', 0)
    accel = velocity.get('acceleration', 0)
    active = velocity.get('active_days', 0)
    lines.append(f'**{cpd} commits/day** · {active} active days · acceleration: {accel:+.0%} *[source: measured]*')
    fv = velocity.get('first_half_vel', 0)
    sv = velocity.get('second_half_vel', 0)
    if fv and sv:
        trend = 'accelerating' if sv > fv else 'decelerating' if sv < fv else 'steady'
        lines.append(f'- early: {fv}/day → recent: {sv}/day ({trend})')
    lines.append('')

    # intent trajectory
    lines.append('## Intent Trajectory\n')
    dom = trajectory.get('dominant', 'unknown')
    lines.append(f'**Dominant: `{dom}`** *[source: measured]*')
    emerging = trajectory.get('emerging', [])
    declining = trajectory.get('declining', [])
    if emerging:
        lines.append(f'- **emerging:** {", ".join(f"`{e}`" for e in emerging)}')
    if declining:
        lines.append(f'- **declining:** {", ".join(f"`{d}`" for d in declining)}')
    trends = trajectory.get('trends', {})
    if trends:
        lines.append('\n| Intent | Trend |')
        lines.append('|---|---|')
        for cat, delta in sorted(trends.items(), key=lambda x: abs(x[1]), reverse=True):
            arrow = '↑' if delta > 0 else '↓' if delta < 0 else '→'
            lines.append(f'| `{cat}` | {arrow} {delta:+.3f} |')
    lines.append('')

    # forward projection
    lines.append('## Forward Projection\n')
    week = projection.get('week', {})
    month = projection.get('month', {})
    quarter = projection.get('quarter', {})

    lines.append(f'### 1 Week *[confidence: {week.get("confidence", "?")}]*')
    lines.append(f'- ~{week.get("estimated_commits", 0)} commits expected')
    lines.append(f'- primary: `{week.get("primary_intent", "?")}`')
    if week.get('secondary_intent'):
        lines.append(f'- secondary: `{week.get("secondary_intent", "?")}`')
    lines.append('')

    lines.append(f'### 1 Month *[confidence: {month.get("confidence", "?")}]*')
    lines.append(f'- ~{month.get("estimated_commits", 0)} commits expected')
    lines.append(f'- primary: `{month.get("primary_intent", "?")}`')
    if month.get('abandoned_risk'):
        lines.append(f'- **risk of abandonment:** `{month["abandoned_risk"]}`')
    lines.append('')

    lines.append(f'### 3 Months *[confidence: {quarter.get("confidence", "?")}]*')
    lines.append(f'- primary: `{quarter.get("primary_intent", "?")}`')
    if quarter.get('emerging_themes'):
        lines.append(f'- **from deleted words:** {", ".join(f"`{t}`" for t in quarter["emerging_themes"])}')
    if quarter.get('module_prediction'):
        lines.append(f'- predicted module focus: {", ".join(f"`{m}`" for m in quarter["module_prediction"])}')
    lines.append('')

    # prompt archaeology
    deleted = patterns.get('deleted_themes', [])
    if deleted:
        lines.append('## Deleted Thought Archaeology\n')
        lines.append('*Words deleted from prompts before submit — the unsaid intent:*\n')
        unique = list(dict.fromkeys(deleted))[:15]
        for w in unique:
            lines.append(f'- "{w}"')
        lines.append('')

    # project management directives
    lines.append('## Project Management Directives\n')
    lines.append(f'*{len(coaching)} directives · auto-generated per push*\n')
    for d in coaching:
        lines.append(f'- {d}')
    lines.append('')

    # testable predictions
    lines.append('## Testable Predictions\n')
    lines.append('*Pass/fail on next push:*\n')
    lines.append(f'1. Dominant intent remains `{dom}` — or shifts to `{emerging[0] if emerging else "?"}`')
    lines.append(f'2. Velocity {"holds above" if cpd > 2 else "stays below"} {cpd:.0f} commits/day')
    if deleted:
        lines.append(f'3. One of [{", ".join(f"`{d}`" for d in list(dict.fromkeys(deleted))[:3])}] appears in next prompt')
    if quarter.get('module_prediction'):
        top_mod = quarter['module_prediction'][0]
        lines.append(f'4. `{top_mod}` gets edited within 2 pushes')

    return '\n'.join(lines)


# ── §6 injection into copilot-instructions ────

def _inject_simulation(root: Path, coaching: list[str], projection: dict) -> None:
    """Inject a compact intent simulation block into copilot-instructions.md."""
    ci_path = root / '.github' / 'copilot-instructions.md'
    if not ci_path.exists():
        return

    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    week = projection.get('week', {})
    month = projection.get('month', {})
    quarter = projection.get('quarter', {})

    lines = [
        '<!-- pigeon:intent-simulation -->',
        '## Intent Simulation',
        '',
        f'*Auto-generated {now} · zero LLM calls*',
        '',
        f'**1 week:** `{week.get("primary_intent", "?")}` (conf={week.get("confidence", "?")}) — ~{week.get("estimated_commits", 0)} commits',
        f'**1 month:** `{month.get("primary_intent", "?")}` (conf={month.get("confidence", "?")}) — ~{month.get("estimated_commits", 0)} commits',
        f'**3 months:** `{quarter.get("primary_intent", "?")}` (conf={quarter.get("confidence", "?")}) — themes: {", ".join(quarter.get("emerging_themes", [])[:3]) or "none"}',
        '',
    ]

    if coaching:
        lines.append('**PM Directives:**')
        for d in coaching[:5]:
            lines.append(f'- {d}')
        lines.append('')

    lines.append('<!-- /pigeon:intent-simulation -->')
    block = '\n'.join(lines)

    content = ci_path.read_text(encoding='utf-8')
    start_tag = '<!-- pigeon:intent-simulation -->'
    end_tag = '<!-- /pigeon:intent-simulation -->'
    start_idx = content.find(start_tag)
    end_idx = content.find(end_tag)

    if start_idx >= 0 and end_idx >= 0:
        content = content[:start_idx] + block + content[end_idx + len(end_tag):]
    else:
        # insert before predictions block
        pred_marker = '<!-- pigeon:predictions -->'
        pred_idx = content.find(pred_marker)
        if pred_idx >= 0:
            content = content[:pred_idx] + block + '\n\n' + content[pred_idx:]
        else:
            content += '\n\n' + block

    ci_path.write_text(content, encoding='utf-8')


# ── §7 public API ─────────────────────────────

def simulate_intent(root: Path, inject: bool = True) -> Path:
    """Run the full intent simulation. Returns path to report.

    Called per push by git_plugin — reads development timeline,
    prompt patterns, cognitive load, projects operator intent forward.
    """
    root = Path(root)

    # gather data
    commits = _git_log(root, days=30)
    journal = _load_journal(root, n=100)
    heat = _load_json(root / 'file_heat_map.json') or {}

    # analyze
    velocity = _analyze_velocity(commits)
    signals = _extract_intent_signals(commits)
    trajectory = _compute_intent_trajectory(signals)
    patterns = _analyze_prompt_patterns(journal)

    # project forward
    projection = _project_forward(velocity, trajectory, patterns)

    # synthesize coaching
    coaching = _synthesize_coaching(projection, patterns, velocity)

    # write report
    report_text = _format_report(velocity, trajectory, patterns, projection, coaching, commits)
    out = root / 'docs' / 'INTENT_SIMULATION.md'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report_text + '\n', encoding='utf-8')

    # save raw projection as JSON for downstream consumers (operator_probes_seq001_v001)
    proj_out = root / 'logs' / 'intent_projection.json'
    proj_out.parent.mkdir(parents=True, exist_ok=True)
    proj_out.write_text(json.dumps({
        'ts': datetime.now(timezone.utc).isoformat(),
        'velocity': velocity,
        'trajectory': trajectory,
        'projection': projection,
        'coaching': coaching,
        'patterns': {
            'module_focus': patterns.get('module_focus', {}),
            'deleted_themes': patterns.get('deleted_themes', []),
            'intent_distribution': patterns.get('intent_distribution', {}),
        },
    }, indent=2, ensure_ascii=False), encoding='utf-8')

    # inject compact version into copilot-instructions
    if inject:
        _inject_simulation(root, coaching, projection)

    return out


if __name__ == '__main__':
    from pathlib import Path
    p = simulate_intent(Path('.'))
    print(f'Intent simulation written to {p}')
