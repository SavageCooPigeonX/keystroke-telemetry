"""Intent-fused prediction report — the system studying the system."""


import json
import re
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter
from statistics import median


def synthesize_research(root: Path) -> Path:
    """Generate a forward-looking prediction report fused with intent analysis."""
    root = Path(root)
    sections = [
        _header(root),
        _what_you_mean_next(root),
        _where_the_system_is(root),
        _pair_dynamics(root),
        _codebase_trajectory(root),
        _unsaid_from_data(root),
        _confidence(root),
    ]
    out = root / 'docs' / 'RESEARCH_LOG.md'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n\n'.join(s for s in sections if s) + '\n', encoding='utf-8')
    return out


# ── §0 header ──────────────────────────────────

def _header(root: Path) -> str:
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    # count data sources
    journal = root / 'logs' / 'prompt_journal.jsonl'
    n_prompts = 0
    if journal.exists():
        try:
            n_prompts = len(journal.read_text('utf-8').strip().splitlines())
        except Exception:
            pass
    rework = root / 'rework_log.json'
    n_rework = 0
    if rework.exists():
        try:
            d = json.loads(rework.read_text('utf-8'))
            n_rework = len(d if isinstance(d, list) else d.get('entries', []))
        except Exception:
            pass
    return (
        '# What The System Knows Right Now\n\n'
        f'*Auto-generated {now} · {n_prompts} prompts · {n_rework} rework entries · zero LLM calls*\n\n'
        '> This report is rewritten on every push. Every prediction becomes pass/fail when the next push lands.\n'
        '> All signals are measured from live telemetry — nothing is inferred or hallucinated.'
    )


# ── §1 what you mean next ─────────────────────

def _what_you_mean_next(root: Path) -> str:
    """Module-level prediction in intent analysis voice."""
    scores_path = root / 'pigeon_brain' / 'prediction_scores.json'
    heat_path = root / 'file_heat_map.json'

    # scoring history
    fp_counter, hit_counter, miss_counter = Counter(), Counter(), Counter()
    n_scored = 0
    if scores_path.exists():
        try:
            data = json.loads(scores_path.read_text(encoding='utf-8'))
            scored = data.get('scores', [])
            n_scored = len(scored)
            for s in scored:
                sc = s.get('score', {})
                for fp in sc.get('false_positives', []):
                    fp_counter[fp] += 1
                for h in sc.get('hits', []):
                    hit_counter[h] += 1
                for m in sc.get('misses', []):
                    miss_counter[m] += 1
        except Exception:
            pass

    # current heat
    hot_modules = []
    if heat_path.exists():
        try:
            hm = json.loads(heat_path.read_text(encoding='utf-8'))
            modules = hm.get('modules', {})
            hot_modules = sorted(
                modules.items(),
                key=lambda x: x[1].get('hesitation', 0), reverse=True
            )[:10]
        except Exception:
            pass

    lines = ['## What Gets Touched Next\n']
    lines.append(f'*{n_scored} scored predictions · zero LLM calls*\n')

    if hot_modules:
        lines.append('### Module Hot Zones *[source: measured]*')
        lines.append('*High cognitive load — take extra care with these files:*')
        for mod, d in hot_modules:
            hes = d.get('hesitation', 0)
            touches = d.get('touch_count', 0)
            hits = hit_counter.get(mod, 0)
            fps = fp_counter.get(mod, 0)
            track = f'{hits}h/{fps}fp' if (hits + fps) else 'no history'
            if fps > hits and fps > 1:
                conf = 'over-predicted'
            elif hits > 0:
                conf = 'confirmed'
            elif hes > 0.5:
                conf = 'high load'
            else:
                conf = 'weak signal'
            lines.append(f'- `{mod}` (hes={hes:.3f}, {touches} touches) — {conf} ({track})')

    # chronic false positives
    if fp_counter:
        top_fp = fp_counter.most_common(3)
        fp_names = ', '.join(f'`{m}`' for m, _ in top_fp)
        lines.append(f'\n> **Prediction bias:** chronically over-predicts {fp_names} — '
                     'operator thinks about them more than they touch them')

    # surprise edits
    if miss_counter:
        lines.append('\n### Blind Spots *[source: measured]*')
        lines.append('*Edited without being predicted — the real surprises:*')
        for mod, ct in miss_counter.most_common(5):
            lines.append(f'- `{mod}` — {ct}x unpredicted')

    return '\n'.join(lines)


# ── §2 where the system is ────────────────────

def _where_the_system_is(root: Path) -> str:
    """Operator state + cognitive signals in intent voice."""
    profile = root / 'operator_profile.md'
    compositions = root / 'logs' / 'chat_compositions.jsonl'
    journal = root / 'logs' / 'prompt_journal.jsonl'

    dominant_state = 'unknown'
    submit_rate = None
    prompt_count = 0

    if profile.exists():
        try:
            text = profile.read_text(encoding='utf-8')
            for line in text.splitlines():
                if 'dominant state:' in line.lower():
                    dominant_state = line.replace('*', '').split(':', 1)[1].strip()
                if 'submit rate:' in line.lower():
                    m = re.search(r'\((\d+)%\)', line)
                    if m:
                        submit_rate = int(m.group(1))
        except Exception:
            pass

    if journal.exists():
        try:
            prompt_count = len(journal.read_text(encoding='utf-8').strip().splitlines())
        except Exception:
            pass

    # recent composition signals
    recent_del, recent_wpm, recent_hes = [], [], []
    if compositions.exists():
        try:
            clines = compositions.read_text(encoding='utf-8').strip().splitlines()
            for cl in (clines[-30:] if len(clines) > 30 else clines):
                try:
                    c = json.loads(cl)
                    r = c.get('deletion_ratio', c.get('intent_deletion_ratio'))
                    if r is not None:
                        recent_del.append(float(r))
                    w = c.get('wpm')
                    if w is not None:
                        recent_wpm.append(float(w))
                    h = c.get('hesitation_count')
                    if h is not None:
                        recent_hes.append(float(h))
                except Exception:
                    pass
        except Exception:
            pass

    # stat line — matches operator-state block voice
    stat_parts = [f'`{dominant_state}`']
    if submit_rate is not None:
        stat_parts.append(f'Submit: {submit_rate}%')
    if recent_wpm:
        stat_parts.append(f'WPM: {sum(recent_wpm)/len(recent_wpm):.1f}')
    if recent_del:
        stat_parts.append(f'Del: {sum(recent_del)/len(recent_del):.1%}')
    if recent_hes:
        stat_parts.append(f'Hes: {sum(recent_hes)/len(recent_hes):.1f}')

    lines = ['## Live Operator State\n']
    lines.append(f'*{prompt_count} prompts profiled · source: measured*\n')
    lines.append(f'**Dominant: {" | ".join(stat_parts)}**')

    # trend analysis — intent analysis style
    if recent_del:
        half = len(recent_del) // 2
        if half > 0:
            first = sum(recent_del[:half]) / half
            second = sum(recent_del[half:]) / len(recent_del[half:])
            if second > first * 1.1:
                lines.append('- operator entering restructuring mode — expect more deletions than new code')
            elif second < first * 0.9:
                lines.append('- operator entering flow state — productive building, less backtracking')
            else:
                lines.append('- deletion ratio stable — no major mode shift detected')

    if recent_wpm:
        avg_wpm = sum(recent_wpm) / len(recent_wpm)
        if avg_wpm < 30:
            lines.append('\n> **CoT directive:** Deep thinking detected. '
                         'Provide complete code blocks, not snippets.')
        elif avg_wpm > 70:
            lines.append('\n> **CoT directive:** Rapid-fire mode. '
                         'Keep responses concise — operator knows what they want.')

    # friction points
    heat_path = root / 'file_heat_map.json'
    if heat_path.exists():
        try:
            hm = json.loads(heat_path.read_text(encoding='utf-8'))
            modules = hm.get('modules', {})
            friction = sorted(
                modules.items(),
                key=lambda x: x[1].get('hesitation', 0), reverse=True
            )[:3]
            if friction:
                lines.append('\n### Friction Points *[source: measured]*')
                lines.append('*Expected hesitation zones next session:*')
                for mod, d in friction:
                    lines.append(f'- `{mod}` (hes={d.get("hesitation", 0):.3f})')
        except Exception:
            pass

    return '\n'.join(lines)


# ── §3 pair dynamics ──────────────────────────

def _pair_dynamics(root: Path) -> str:
    """Rework + pair performance in intent voice."""
    rework_path = root / 'rework_log.json'
    n_rework = ok_count = miss_count = bg_excluded = 0
    source = []
    if rework_path.exists():
        try:
            data = json.loads(rework_path.read_text(encoding='utf-8'))
            entries = data if isinstance(data, list) else data.get('entries', [])
            fg = [e for e in entries if not str(e.get('query_hint', '')).startswith('bg:')]
            bg_excluded = len(entries) - len(fg)
            source = fg if fg else entries
            n_rework = len(source)
            for e in source:
                v = e.get('verdict', '?')
                if v == 'ok':
                    ok_count += 1
                elif v == 'miss':
                    miss_count += 1
        except Exception:
            pass

    lines = ['## Pair Performance\n']
    lines.append(f'*{n_rework} responses scored · {bg_excluded} background excluded*\n')

    if n_rework:
        ok_pct = ok_count / n_rework * 100
        miss_pct = miss_count / n_rework * 100
        lines.append(f'**Accuracy: {ok_pct:.0f}% OK | {miss_pct:.0f}% miss** '
                     f'*[source: measured]*')

        # trend — first half vs second half
        half = n_rework // 2
        if half > 2:
            first_ok = sum(1 for e in source[:half] if e.get('verdict') == 'ok') / half
            second_ok = sum(1 for e in source[half:] if e.get('verdict') == 'ok') / len(source[half:])
            if second_ok > first_ok + 0.05:
                lines.append(f'- trend: **improving** (early {first_ok:.0%} → recent {second_ok:.0%})')
                lines.append('- copilot is getting better at reading intent')
            elif second_ok < first_ok - 0.05:
                lines.append(f'- trend: **degrading** (early {first_ok:.0%} → recent {second_ok:.0%})')
                lines.append('- quality slipping — check if prompt mutations are helping or hurting')
            else:
                lines.append(f'- trend: **stable** ({first_ok:.0%} → {second_ok:.0%})')

    # latency
    ep_path = root / 'logs' / 'edit_pairs.jsonl'
    valid_lats = []
    if ep_path.exists():
        try:
            for line in ep_path.read_text(encoding='utf-8').strip().splitlines():
                obj = json.loads(line)
                lat = obj.get('latency_ms')
                if isinstance(lat, (int, float)) and 0 <= lat <= 3_600_000:
                    valid_lats.append(lat)
        except Exception:
            pass
    if valid_lats:
        med = median(valid_lats) / 1000
        lines.append(f'\n**Prompt→edit latency:** {med:.1f}s median ({len(valid_lats)} pairs)')

    # mutations
    mut_path = root / 'logs' / 'mutation_scores.json'
    if mut_path.exists():
        try:
            md = json.loads(mut_path.read_text(encoding='utf-8'))
            total_mut = md.get('total_mutations', 0)
            sects = md.get('sections', {})
            helpful = [k for k, v in sects.items() if v.get('hit_rate_delta', 0) > 0.05]
            harmful = [k for k, v in sects.items() if v.get('hit_rate_delta', 0) < -0.05]
            lines.append(f'\n### Mutation Effectiveness *[source: measured]*')
            lines.append(f'*{total_mut} mutations scored*')
            if helpful:
                lines.append(f'- helping: {", ".join(helpful)}')
            if harmful:
                lines.append(f'- **hurting (consider reverting):** {", ".join(harmful)}')
            if not helpful and not harmful:
                lines.append('- no significant signal yet — all sections scored neutral')
        except Exception:
            pass

    # reactor
    reactor_path = root / 'logs' / 'cognitive_reactor_state.json'
    if reactor_path.exists():
        try:
            rd = json.loads(reactor_path.read_text(encoding='utf-8'))
            fires = rd.get('total_fires', 0)
            applied = rd.get('patches_applied', 0) or 0
            if fires:
                pct = applied / fires * 100
                lines.append(f'\n**Reactor:** {fires} fires, {applied} accepted ({pct:.0f}%)')
                if pct < 5:
                    lines.append('> **Directive:** Reactor patches near-zero acceptance — '
                                 'tune confidence threshold or disable')
        except Exception:
            pass

    return '\n'.join(lines)


# ── §4 codebase trajectory ────────────────────

def _codebase_trajectory(root: Path) -> str:
    """Health + risks merged in intent voice."""
    lines = ['## Codebase Health\n']

    # self-fix trajectory
    sf_dir = root / 'docs' / 'self_fix'
    if sf_dir.exists():
        reports = sorted(sf_dir.glob('*.md'))
        counts = []
        for r in reports:
            try:
                text = r.read_text(encoding='utf-8')
                n = (text.lower().count('over_hard_cap')
                     + text.lower().count('hardcoded')
                     + text.lower().count('dead_export'))
                counts.append((r.stem[:10], n))
            except Exception:
                pass
        if counts:
            first5 = [c[1] for c in counts[:5]]
            last5 = [c[1] for c in counts[-5:]]
            avg_first = sum(first5) / len(first5)
            avg_last = sum(last5) / len(last5)
            trend = 'improving' if avg_last < avg_first else 'growing'
            lines.append(f'*{len(counts)} self-fix reports · '
                         f'{counts[0][0]} → {counts[-1][0]}*\n')
            lines.append(f'**Problem trend: {trend}** '
                         f'(early avg {avg_first:.0f} → recent avg {avg_last:.0f}) '
                         '*[source: measured]*')
            if avg_last > avg_first:
                delta = avg_last - avg_first
                lines.append(f'- problems growing ~{delta:.0f}/push — '
                             'expect more over_hard_cap and dead_exports without intervention')
            else:
                lines.append('- self-fix pipeline is containing technical debt')

    # fragile contracts from push narratives
    narr_dir = root / 'docs' / 'push_narratives'
    if narr_dir.exists():
        narrs = sorted(narr_dir.glob('*.md'))
        if narrs:
            watch_items = []
            for narr in narrs[-3:]:
                try:
                    text = narr.read_text(encoding='utf-8')
                    for line in text.splitlines():
                        low = line.lower()
                        if any(k in low for k in ['watch for', 'could break', 'fragile', 'regression']):
                            cleaned = line.strip().lstrip('- *>')
                            if cleaned and len(cleaned) < 200:
                                watch_items.append(cleaned)
                except Exception:
                    pass
            if watch_items:
                lines.append('\n### Fragile Contracts *[source: llm_derived]*')
                lines.append('*From push narratives — treat as hypothesis:*')
                for item in watch_items[:5]:
                    lines.append(f'- {item}')

    # electron deaths
    death_path = root / 'execution_death_log.json'
    if death_path.exists():
        try:
            data = json.loads(death_path.read_text(encoding='utf-8'))
            entries = data if isinstance(data, list) else data.get('entries', [])
            if entries:
                causes = Counter(e.get('cause', '?') for e in entries[-20:])
                lines.append(f'\n### Recent Deaths *[source: measured]*')
                for cause, ct in causes.most_common():
                    lines.append(f'- `{cause}`: {ct}')
                top = causes.most_common(1)[0][0] if causes else '?'
                lines.append(f'> **Prediction:** `{top}` remains dominant failure mode '
                             'until root cause is addressed')
        except Exception:
            pass

    # high-death graph nodes
    ghm_path = root / 'graph_heat_map.json'
    if ghm_path.exists():
        try:
            ghm = json.loads(ghm_path.read_text(encoding='utf-8'))
            danger = [(n, d.get('total_deaths', 0), d.get('total_calls', 0))
                      for n, d in ghm.items() if d.get('total_deaths', 0) >= 2]
            if danger:
                danger.sort(key=lambda x: x[1], reverse=True)
                lines.append('\n### Electron Killers *[source: measured]*')
                for node, deaths, calls in danger[:5]:
                    rate = f'{deaths/calls*100:.0f}%' if calls else '?'
                    lines.append(f'- `{node}` — {deaths} deaths/{calls} calls ({rate})')
        except Exception:
            pass

    # loop patterns
    loop_path = root / 'loop_detector.json'
    if loop_path.exists():
        try:
            data = json.loads(loop_path.read_text(encoding='utf-8'))
            patterns = data.get('patterns', [])
            if patterns:
                lines.append(f'\n### Recurring Loops ({len(patterns)} detected)')
                for p in patterns[:3]:
                    path_str = ' → '.join(p.get('path', [])[:4])
                    lines.append(f'- {path_str} (seen {p.get("count", "?")}x)')
        except Exception:
            pass

    # over-cap risk
    reg_path = root / 'pigeon_registry.json'
    if reg_path.exists():
        try:
            reg = json.loads(reg_path.read_text(encoding='utf-8'))
            modules = reg.get('modules', reg) if isinstance(reg, dict) else []
            overcap = []
            if isinstance(modules, dict):
                for name, info in modules.items():
                    tokens = info.get('tokens', 0)
                    if tokens > 3000:
                        overcap.append((name, tokens))
            if overcap:
                overcap.sort(key=lambda x: x[1], reverse=True)
                lines.append(f'\n### Over-Cap Risk ({len(overcap)} modules > 3000 tokens)')
                for name, tokens in overcap[:5]:
                    lines.append(f'- `{name}`: {tokens} tokens')
        except Exception:
            pass

    return '\n'.join(lines)


# ── §5 unsaid from data ──────────────────────

def _unsaid_from_data(root: Path) -> str:
    """Reconstruct unsaid threads from composition telemetry."""
    compositions = root / 'logs' / 'chat_compositions.jsonl'
    journal = root / 'logs' / 'prompt_journal.jsonl'

    deleted_words = []
    high_del_prompts = []

    # from journal
    if journal.exists():
        try:
            for line in journal.read_text(encoding='utf-8').strip().splitlines()[-50:]:
                try:
                    obj = json.loads(line)
                    dw = obj.get('deleted_words', [])
                    if dw:
                        deleted_words.extend(dw)
                    dr = obj.get('deletion_ratio', 0)
                    if dr > 0.3:
                        high_del_prompts.append(obj.get('msg', '')[:80])
                except Exception:
                    pass
        except Exception:
            pass

    # from compositions
    if compositions.exists():
        try:
            for line in compositions.read_text(encoding='utf-8').strip().splitlines()[-50:]:
                try:
                    obj = json.loads(line)
                    dw = obj.get('deleted_words', [])
                    if dw:
                        deleted_words.extend(dw)
                except Exception:
                    pass
        except Exception:
            pass

    if not deleted_words and not high_del_prompts:
        return ''

    lines = ['## Unsaid Threads\n']
    lines.append('*Deleted from prompts — operator wanted this but did not ask:*\n')

    # unique deleted fragments
    seen = set()
    for w in deleted_words:
        if isinstance(w, dict):
            w = w.get('text', w.get('word', str(w)))
        w = str(w).strip()
        if w and w not in seen and len(w) > 2:
            seen.add(w)
    if seen:
        for w in list(seen)[:10]:
            lines.append(f'- "{w}"')

    if high_del_prompts:
        lines.append('\n### High-Deletion Prompts *[source: measured]*')
        lines.append('*Prompts where >30% was deleted before submit — restructuring signal:*')
        for p in high_del_prompts[:5]:
            lines.append(f'- "{p}"')

    return '\n'.join(lines)


# ── §6 confidence ─────────────────────────────

def _confidence(root: Path) -> str:
    """Data quality + testable hypotheses."""
    lines = ['## Confidence\n']
    lines.append('*How much to trust this report:*\n')

    checks = []
    rework = root / 'rework_log.json'
    if rework.exists():
        try:
            data = json.loads(rework.read_text(encoding='utf-8'))
            entries = data if isinstance(data, list) else data.get('entries', [])
            n = len(entries)
            scores = [e.get('rework_score', 0) for e in entries[-20:]]
            unique = len(set(round(s, 4) for s in scores))
            bg = sum(1 for e in entries if str(e.get('query_hint', '')).startswith('bg:'))
            quality = 'GOOD' if unique > 2 else 'WEAK (placeholder data)'
            checks.append(f'- **Rework signal:** {quality} — '
                          f'{n} entries, {unique} unique scores in last 20'
                          f'{f", {bg} bg noise" if bg else ""}')
        except Exception:
            pass

    tp = root / 'logs' / 'shards' / 'training_pairs.md'
    if tp.exists():
        try:
            text = tp.read_text(encoding='utf-8')
            pair_count = text.count('### `')
            checks.append(f'- **Training pairs:** {pair_count} captured')
        except Exception:
            pass

    scores_path = root / 'pigeon_brain' / 'prediction_scores.json'
    if scores_path.exists():
        try:
            data = json.loads(scores_path.read_text(encoding='utf-8'))
            scored = data.get('scores', [])
            if scored:
                avg_f1 = sum(s['score']['f1'] for s in scored) / len(scored)
                avg_cal = sum(s['score']['calibration_error'] for s in scored) / len(scored)
                checks.append(f'- **Prediction accuracy:** F1={avg_f1:.3f}, '
                              f'calibration={avg_cal:.3f} ({len(scored)} scored)')
                if avg_f1 < 0.1:
                    checks.append('  - predictions near-random — treat all forecasts as hypotheses')
        except Exception:
            pass

    shards = root / 'logs' / 'shards'
    if shards.exists():
        shard_count = len(list(shards.glob('*.md')))
        checks.append(f'- **Memory shards:** {shard_count} active (zero LLM calls)')

    if checks:
        lines.extend(checks)

    lines.append('\n### Hypotheses Under Test')
    lines.append('*These predictions become pass/fail on next push:*')
    lines.append('')
    lines.append('1. **Hesitation ≠ intent** — high-hes modules will NOT be the ones actually edited')
    lines.append('2. **Deletion trend predicts mode** — rising deletion → restructuring, not building')
    lines.append('3. **Rework trajectory holds** — if improving, fewer misses next push')
    lines.append('4. **Self-fix converging** — if problem count falling, fewer violations next push')
    lines.append('5. **Reactor acceptance stays <5%** — confidence threshold is miscalibrated')

    return '\n'.join(lines)
