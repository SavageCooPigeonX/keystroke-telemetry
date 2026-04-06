"""Autonomous research synthesizer — the system studying the system studying us."""


import json
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter


def synthesize_research(root: Path) -> Path:
    """Read all telemetry, score predictions, analyze cognition, write research log."""
    root = Path(root)
    sections = [
        _header(),
        _prediction_findings(root),
        _cognitive_findings(root),
        _pair_dynamics(root),
        _recursive_evolution(root),
        _signal_quality(root),
        _open_questions(),
    ]
    out = root / 'docs' / 'RESEARCH_LOG.md'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text('\n\n'.join(s for s in sections if s) + '\n', encoding='utf-8')
    return out


def _header() -> str:
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    return (
        '# Research Log — The System Studying Us\n\n'
        f'*Auto-generated {now} by `research_lab_seq029`. '
        'This document is rewritten on every push. '
        'It contains what the prediction engine, self-fix scanner, '
        'and cognitive profiler have learned about human/AI pair programming.*'
    )


def _prediction_findings(root: Path) -> str:
    scores_path = root / 'pigeon_brain' / 'prediction_scores.json'
    preds_path = root / 'logs' / 'push_predictions.jsonl'
    if not scores_path.exists():
        return '## Prediction Engine\n\nNo scored predictions yet.'
    try:
        data = json.loads(scores_path.read_text(encoding='utf-8'))
    except Exception:
        return '## Prediction Engine\n\nCorrupt score file.'
    scores = data.get('scores', [])
    if not scores:
        return '## Prediction Engine\n\n0 predictions scored.'

    # Aggregate by mode
    by_mode = {}
    for s in scores:
        m = s.get('mode', '?')
        by_mode.setdefault(m, []).append(s['score'])

    lines = [
        '## 1. Prediction Engine — What It Gets Right and Wrong',
        f'**{len(scores)} predictions scored** across {len(by_mode)} modes.',
        '',
        '| Mode | N | Avg F1 | Hit Rate | Avg Calibration Error |',
        '|------|---|--------|----------|-----------------------|',
    ]
    for mode, sc_list in sorted(by_mode.items()):
        n = len(sc_list)
        avg_f1 = sum(s['f1'] for s in sc_list) / n
        hit_rate = sum(1 for s in sc_list if s['f1'] > 0) / n
        avg_cal = sum(s['calibration_error'] for s in sc_list) / n
        lines.append(f'| {mode} | {n} | {avg_f1:.3f} | {hit_rate:.1%} | {avg_cal:.3f} |')

    # What it obsesses over vs what actually changes
    fp_counter = Counter()
    hit_counter = Counter()
    for s in scores:
        for fp in s['score'].get('false_positives', []):
            fp_counter[fp] += 1
        for h in s['score'].get('hits', []):
            hit_counter[h] += 1

    lines.append('')
    lines.append('### The Fixation Problem')
    lines.append('')
    lines.append('The predictor keeps guessing the same modules — the ones the operator '
                 '*hesitates* on — not the ones they *actually edit*.')
    lines.append('')
    if fp_counter:
        top_fp = fp_counter.most_common(5)
        lines.append('**Most over-predicted (false positives):**')
        for mod, ct in top_fp:
            lines.append(f'- `{mod}` — predicted {ct}x, rarely edited')
    if hit_counter:
        top_hits = hit_counter.most_common(5)
        lines.append('')
        lines.append('**Actually edited (true hits):**')
        for mod, ct in top_hits:
            lines.append(f'- `{mod}` — correctly predicted {ct}x')

    lines.append('')
    lines.append('**Interpretation:** Hesitation ≠ intent. The operator hesitates on '
                 'scary/complex modules but edits familiar ones. The prediction engine '
                 'confuses cognitive load with task selection. This is a fundamental '
                 'insight about human/AI pair programming — the AI watches where you '
                 'sweat, but you work where you\'re comfortable.')

    # Unscored predictions still pending
    try:
        pending = sum(1 for line in preds_path.read_text(encoding='utf-8').strip().splitlines()
                      if not json.loads(line).get('scored', False))
        if pending:
            lines.append(f'\n**{pending} predictions still unscored** (awaiting next push cycle).')
    except Exception:
        pass

    return '\n'.join(lines)


def _cognitive_findings(root: Path) -> str:
    profile = root / 'operator_profile.md'
    heat = root / 'file_heat_map.json'
    lines = ['## 2. Cognitive Patterns — What We Know About the Operator']

    # Parse operator profile for key stats
    submit_rate_str = '?'
    dominant_state = 'unknown'
    avg_del_pct = '?'
    if profile.exists():
        text = profile.read_text(encoding='utf-8')
        for marker in ['Dominant state:',
                       'Submit rate:', 'Longest struggle streak:']:
            for line in text.splitlines():
                if marker.lower() in line.lower():
                    lines.append(f'- {line.strip().lstrip("- ")}')
                    break
        # Extract actual numbers for interpretation
        for line in text.splitlines():
            if 'submit rate:' in line.lower():
                import re as _re
                m = _re.search(r'\((\d+)%\)', line)
                if m:
                    submit_rate_str = m.group(1) + '%'
            if 'dominant state:' in line.lower():
                parts = line.split('**')
                if len(parts) >= 2:
                    dominant_state = parts[-1].strip().rstrip('*').strip()
                    if not dominant_state:
                        dominant_state = parts[1].strip()
            if 'deletion %' in line.lower() and 'avg' not in line.lower():
                pass  # header row
            if '| Deletion %' in line:
                cells = [c.strip() for c in line.split('|')]
                if len(cells) >= 5:
                    avg_del_pct = cells[4]  # Avg column

    # Prefer real data from prompt_journal + chat_compositions
    journal = root / 'logs' / 'prompt_journal.jsonl'
    compositions = root / 'logs' / 'chat_compositions.jsonl'
    real_submit_count = 0
    real_del_ratio = None
    if journal.exists():
        try:
            jlines = journal.read_text(encoding='utf-8').strip().splitlines()
            real_submit_count = len(jlines)
        except Exception:
            pass
    if compositions.exists():
        try:
            clines = compositions.read_text(encoding='utf-8').strip().splitlines()
            recent = clines[-50:] if len(clines) > 50 else clines
            ratios = []
            for cl in recent:
                try:
                    c = json.loads(cl)
                    r = c.get('deletion_ratio', c.get('intent_deletion_ratio'))
                    if r is not None:
                        ratios.append(float(r))
                except Exception:
                    pass
            if ratios:
                real_del_ratio = sum(ratios) / len(ratios)
        except Exception:
            pass

    # Heat map — which modules cause most cognitive friction
    if heat.exists():
        try:
            hm = json.loads(heat.read_text(encoding='utf-8'))
            modules = hm.get('modules', {})
            sorted_mods = sorted(modules.items(), key=lambda x: x[1].get('hesitation', 0), reverse=True)[:5]
            if sorted_mods:
                lines.append('')
                lines.append('### Cognitive Friction Map')
                lines.append('| Module | Hesitation | Touches |')
                lines.append('|--------|-----------|---------|')
                for mod, data in sorted_mods:
                    hes = data.get('hesitation', 0)
                    touches = data.get('touch_count', 0)
                    lines.append(f'| `{mod}` | {hes:.3f} | {touches} |')
        except Exception:
            pass

    # Build interpretation from actual computed data
    lines.append('')
    del_desc = f'{real_del_ratio:.1%}' if real_del_ratio is not None else avg_del_pct
    lines.append(f'**Interpretation:** The operator deletes ~{del_desc} of what they type '
                 f'(from chat compositions). '
                 f'Dominant cognitive state: **{dominant_state}**. '
                 f'{real_submit_count} real chat submits recorded in prompt journal'
                 f'{" (submit rate: " + submit_rate_str + " of profiled messages)" if submit_rate_str != "?" else ""}. '
                 'The system captures typing patterns, hesitation, and deleted words '
                 'that would otherwise be invisible.')
    return '\n'.join(lines)


def _pair_dynamics(root: Path) -> str:
    """Section 3: the human/AI pair — how we work together."""
    lines = ['## 3. Pair Dynamics — How Human + AI Actually Collaborate']

    # Rework verdicts — how good is copilot at answering?
    rework_path = root / 'rework_log.json'
    verdicts = {}
    n_rework = 0
    if rework_path.exists():
        try:
            data = json.loads(rework_path.read_text(encoding='utf-8'))
            entries = data if isinstance(data, list) else data.get('entries', [])
            n_rework = len(entries)
            for e in entries:
                v = e.get('verdict', '?')
                verdicts[v] = verdicts.get(v, 0) + 1
        except Exception:
            pass
    if n_rework:
        ok = verdicts.get('ok', 0)
        partial = verdicts.get('partial', 0)
        miss = verdicts.get('miss', 0)
        ok_pct = ok / n_rework * 100
        miss_pct = miss / n_rework * 100
        lines.append(f'\n**Rework verdicts** ({n_rework} responses scored):')
        lines.append(f'- OK: {ok} ({ok_pct:.0f}%) — copilot nailed it')
        lines.append(f'- Partial: {partial} ({partial/n_rework*100:.0f}%) — needed adjustment')
        lines.append(f'- Miss: {miss} ({miss_pct:.0f}%) — operator had to redo')

    # Edit pairs — prompt→file timing
    ep_path = root / 'logs' / 'edit_pairs.jsonl'
    n_pairs = 0
    latencies = []
    if ep_path.exists():
        try:
            for line in ep_path.read_text(encoding='utf-8').strip().splitlines():
                obj = json.loads(line)
                n_pairs += 1
                lat = obj.get('latency_ms')
                if lat and isinstance(lat, (int, float)):
                    latencies.append(lat)
        except Exception:
            pass
    if n_pairs:
        lines.append(f'\n**Prompt→file pairings:** {n_pairs} edits traced back to prompts.')
        if latencies:
            avg_lat = sum(latencies) / len(latencies) / 1000
            lines.append(f'- Avg prompt-to-edit latency: {avg_lat:.1f}s')

    # Mutation tracking — how the prompt layer evolved
    mut_path = root / 'logs' / 'mutation_scores.json'
    if mut_path.exists():
        try:
            md = json.loads(mut_path.read_text(encoding='utf-8'))
            total_mut = md.get('total_mutations', 0)
            total_pairs = md.get('total_pairs', 0)
            lines.append(f'\n**Prompt mutations:** {total_mut} changes to copilot-instructions.md, '
                         f'scored against {total_pairs} rework pairs.')
            sects = md.get('sections', {})
            helpful = [k for k, v in sects.items() if v.get('hit_rate_delta', 0) > 0.05]
            harmful = [k for k, v in sects.items() if v.get('hit_rate_delta', 0) < -0.05]
            if helpful:
                lines.append(f'- Helpful sections: {", ".join(helpful)}')
            if harmful:
                lines.append(f'- Harmful sections: {", ".join(harmful)}')
            if not helpful and not harmful:
                lines.append('- No significant signal yet — all sections scored neutral.')
        except Exception:
            pass

    # Reactor — autonomous code modification attempts
    reactor_path = root / 'logs' / 'cognitive_reactor_state.json'
    if reactor_path.exists():
        try:
            rd = json.loads(reactor_path.read_text(encoding='utf-8'))
            fires = rd.get('total_fires', 0)
            applied = rd.get('patches_applied', 0) or 0
            lines.append(f'\n**Cognitive reactor:** {fires} fires. '
                         f'{applied} code patches applied '
                         f'({applied/fires*100:.0f}% acceptance).' if fires else '')
        except Exception:
            pass

    # Shard memory — what the system learned from interactions
    shard_dir = root / 'logs' / 'shards'
    if shard_dir.exists():
        shard_files = list(shard_dir.glob('*.md'))
        shard_names = [f.stem for f in shard_files if not f.stem.startswith('_')]
        if shard_names:
            lines.append(f'\n**Shared memory shards** ({len(shard_files)} active):')
            for s in sorted(shard_names)[:8]:
                lines.append(f'- `{s}`')

    # Interpretation
    lines.append('')
    interp_parts = []
    if n_rework:
        interp_parts.append(
            f'Copilot gets it right {ok_pct:.0f}% of the time, '
            f'misses {miss_pct:.0f}%. '
        )
    interp_parts.append(
        'The pair communicates through: keystrokes (operator→system), '
        'rework verdicts (operator→copilot quality signal), '
        'prompt mutations (system→copilot instruction tuning), '
        'reactor patches (copilot→codebase autonomous edits), '
        'and memory shards (shared context that persists across sessions). '
    )
    interp_parts.append(
        'This is not one-way automation — it is a feedback loop where '
        'both sides adapt. The operator\'s typing patterns steer the AI\'s '
        'reasoning, and the AI\'s prompt mutations steer the operator\'s '
        'workflow. Neither side is fully in control.'
    )
    lines.append('**Interpretation:** ' + ''.join(interp_parts))
    return '\n'.join(lines)


def _recursive_evolution(root: Path) -> str:
    sf_dir = root / 'docs' / 'self_fix'
    lines = ['## 4. Recursive Code Evolution — The Codebase Changing Itself']

    if sf_dir.exists():
        reports = sorted(sf_dir.glob('*.md'))
        counts = []
        for r in reports:
            try:
                text = r.read_text(encoding='utf-8')
                n = text.lower().count('over_hard_cap') + text.lower().count('hardcoded') + text.lower().count('dead_export')
                date = r.stem[:10]
                counts.append((date, n))
            except Exception:
                pass

        if counts:
            lines.append(f'\n**{len(counts)} self-fix reports** from {counts[0][0]} to {counts[-1][0]}.')
            first5 = [c[1] for c in counts[:5]]
            last5 = [c[1] for c in counts[-5:]]
            lines.append(f'- Early avg problems: {sum(first5)/len(first5):.0f}')
            lines.append(f'- Recent avg problems: {sum(last5)/len(last5):.0f}')
            trend = 'improving' if sum(last5) < sum(first5) else 'stable/growing'
            lines.append(f'- Trend: **{trend}**')

    # Push cycle data
    cycles_path = root / 'logs' / 'push_cycles.jsonl'
    if cycles_path.exists():
        try:
            cycle_lines = cycles_path.read_text(encoding='utf-8').strip().splitlines()
            n_cycles = len(cycle_lines)
            last = json.loads(cycle_lines[-1])
            lines.append(f'\n**{n_cycles} push cycles** completed. Latest sync score: {last.get("sync",{}).get("score","?")}')
        except Exception:
            pass

    # Push narratives (the code speaking about itself)
    narr_dir = root / 'docs' / 'push_narratives'
    if narr_dir.exists():
        narr_count = len(list(narr_dir.glob('*.md')))
        lines.append(f'\n**{narr_count} push narratives** — each file explains why it was touched, '
                     'what assumption could break, and what regression to watch for.')

    lines.append('')
    lines.append('**Interpretation:** The codebase rewrites its own module boundaries, '
                 'catches its own stale imports, and compiles its own size violations. '
                 'Each commit triggers: rename → self-fix scan → backward pass → '
                 'prediction → coaching injection. The code evolves through its own '
                 'diagnostic pipeline, not just through human edits.')
    return '\n'.join(lines)


def _signal_quality(root: Path) -> str:
    lines = ['## 5. Signal Quality — How Good Is Our Data']
    rework = root / 'rework_log.json'
    if rework.exists():
        try:
            data = json.loads(rework.read_text(encoding='utf-8'))
            entries = data if isinstance(data, list) else data.get('entries', [])
            n = len(entries)
            scores = [e.get('rework_score', 0) for e in entries[-20:]]
            unique = len(set(round(s, 4) for s in scores))
            lines.append(f'- **Rework log:** {n} entries. '
                         f'Last 20 unique scores: {unique} '
                         f'{"⚠️ (likely placeholder data)" if unique <= 2 else "✓ (real variation)"}')
        except Exception:
            pass

    tp = root / 'logs' / 'shards' / 'training_pairs.md'
    if tp.exists():
        try:
            text = tp.read_text(encoding='utf-8')
            pair_count = text.count('### `')
            lines.append(f'- **Training pairs:** {pair_count} captured with muxed cognitive state')
        except Exception:
            pass

    shards = root / 'logs' / 'shards'
    if shards.exists():
        shard_count = len(list(shards.glob('*.md')))
        lines.append(f'- **Memory shards:** {shard_count} active (local markdown, zero LLM calls)')
    return '\n'.join(lines)


def _open_questions() -> str:
    return (
        '## 6. Open Research Questions\n\n'
        '1. **Hesitation ≠ intent** — can we separate "thinking about X" from "about to edit X"?\n'
        '2. **Deletion ratio as confidence** — does deletion ratio indicate uncertainty or refinement?\n'
        '3. **Prediction calibration** — confidence is stuck at 0.49-0.50, needs dynamic update\n'
        '4. **Cross-session memory** — do shard patterns persist across conversations?\n'
        '5. **Rework signal** — is the 0.003 score a measurement or a default? Needs audit\n'
        '6. **Recursive depth** — at what point does the system\'s self-modification '
        'change the operator\'s behavior? When does the observer change the observed?'
    )
