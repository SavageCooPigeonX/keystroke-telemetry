"""Render the operator intelligence profile as browsable markdown.

Usage:
    py src/tc_intel_report_seq001_v001.py                  # print to stdout
    py src/tc_intel_report_seq001_v001.py -o intel.md      # write to file
    py src/tc_intel_report_seq001_v001.py --section voice  # single shard
    py src/tc_intel_report_seq001_v001.py --secrets        # just the intelligence file
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE_PATH = ROOT / 'logs' / 'operator_profile_tc.json'


def load_profile() -> dict:
    if not PROFILE_PATH.exists():
        return {}
    return json.loads(PROFILE_PATH.read_text('utf-8', errors='ignore'))


def _bar(value: float, width: int = 20) -> str:
    filled = int(value * width)
    return '█' * filled + '░' * (width - filled)


def _top_items(d: dict, n: int = 10) -> list[tuple[str, int]]:
    return sorted(d.items(), key=lambda x: x[1], reverse=True)[:n]


def _pct(num: float, denom: float) -> str:
    if denom == 0:
        return '0%'
    return f'{num / denom:.0%}'


# ── SHARD RENDERERS ──

def render_header(p: dict) -> str:
    lines = [
        '# Operator Intelligence Report',
        '',
        f'*Generated {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")} '
        f'· {p.get("samples", 0)} samples '
        f'· profile created {p.get("created", "?")[:10]}*',
        '',
    ]
    return '\n'.join(lines)


def render_voice(p: dict) -> str:
    v = p.get('shards', {}).get('voice', {})
    if not v.get('top_words'):
        return ''
    lines = ['## Voice', '']
    lines.append(f'**Avg words/msg:** {v.get("avg_words_per_msg", 0):.1f} '
                 f'| **Uses caps:** {v.get("uses_caps", False)} '
                 f'| **Punctuation rate:** {v.get("punct_rate", 0):.1%}')
    lines.append('')

    # top words
    top = _top_items(v.get('top_words', {}), 15)
    if top:
        lines.append('**Top words:**')
        lines.append('| Word | Count |')
        lines.append('|------|-------|')
        for w, c in top:
            lines.append(f'| {w} | {c} |')
        lines.append('')

    # bigrams
    bigrams = _top_items(v.get('bigrams', {}), 10)
    if bigrams:
        lines.append('**Top bigrams:**')
        for b, c in bigrams:
            lines.append(f'- "{b}" ({c}x)')
        lines.append('')

    # catchphrases
    catch = v.get('catchphrases', [])
    if catch:
        lines.append('**Catchphrases:** ' + ', '.join(f'"{c}"' for c in catch[:8]))
        lines.append('')

    # fillers
    fillers = _top_items(v.get('filler_words', {}), 8)
    if fillers:
        lines.append('**Filler words:** ' + ', '.join(f'{w}({c})' for w, c in fillers))
        lines.append('')

    return '\n'.join(lines)


def render_rhythm(p: dict) -> str:
    r = p.get('shards', {}).get('rhythm', {})
    if not r.get('avg_wpm'):
        return ''
    lines = ['## Rhythm', '']
    lines.append(f'| Metric | Value |')
    lines.append(f'|--------|-------|')
    lines.append(f'| Avg WPM | {r.get("avg_wpm", 0):.1f} |')
    lines.append(f'| WPM P25 | {r.get("wpm_p25", 0):.1f} |')
    lines.append(f'| WPM P75 | {r.get("wpm_p75", 0):.1f} |')
    lines.append(f'| Avg deletion ratio | {r.get("avg_del_ratio", 0):.1%} |')
    lines.append(f'| Avg pause before send | {r.get("avg_pause_before_send_ms", 0):.0f}ms |')
    lines.append('')
    hours = r.get('peak_hours_utc', [])
    if hours:
        lines.append(f'**Peak hours (UTC):** {", ".join(str(h) for h in hours[:5])}')
        lines.append('')
    return '\n'.join(lines)


def render_deletions(p: dict) -> str:
    d = p.get('shards', {}).get('deletions', {})
    if not d.get('deleted_words'):
        return ''
    lines = ['## Deletions (The Unsaid Mind)', '']
    lines.append(f'**Abandon rate:** {d.get("abandon_rate", 0):.1%}')
    lines.append('')

    top = _top_items(d.get('deleted_words', {}), 15)
    if top:
        lines.append('**Most deleted words:**')
        lines.append('| Fragment | Count |')
        lines.append('|----------|-------|')
        for w, c in top:
            lines.append(f'| `{w}` | {c} |')
        lines.append('')

    unsaid = d.get('top_unsaid', [])
    if unsaid:
        lines.append('**Top unsaid (complete words deleted):** ' +
                      ', '.join(f'"{u}"' for u in unsaid[:10]))
        lines.append('')

    rewrites = d.get('rewrite_patterns', [])
    if rewrites:
        lines.append('**Rewrite patterns:**')
        for rw in rewrites[:8]:
            if isinstance(rw, (list, tuple)) and len(rw) >= 2:
                lines.append(f'- "{rw[0]}" → "{rw[1]}"')
            else:
                lines.append(f'- {rw}')
        lines.append('')

    return '\n'.join(lines)


def render_topics(p: dict) -> str:
    t = p.get('shards', {}).get('topics', {})
    lines = ['## Topics', '']

    themes = _top_items(t.get('recurring_themes', {}), 10)
    if themes:
        total = sum(c for _, c in themes)
        lines.append('**Recurring themes:**')
        for th, c in themes:
            pct = c / total if total else 0
            lines.append(f'- {th}: {c} ({pct:.0%}) {_bar(pct, 15)}')
        lines.append('')

    mods = _top_items(t.get('module_mentions', {}), 15)
    if mods:
        lines.append('**Module mentions:**')
        for m, c in mods:
            lines.append(f'- `{m}` ({c}x)')
        lines.append('')

    focus = t.get('recent_focus', [])
    if focus:
        lines.append(f'**Recent focus:** {" → ".join(focus[-5:])}')
        lines.append('')

    return '\n'.join(lines)


def render_decisions(p: dict) -> str:
    d = p.get('shards', {}).get('decisions', {})
    if not d.get('total_completions'):
        return ''
    lines = ['## Decisions', '']
    lines.append(f'**Total completions:** {d.get("total_completions", 0)} '
                 f'| **Accept rate:** {d.get("accept_rate", 0):.1%} '
                 f'| **Reward rate:** {d.get("reward_rate", 0):.1%}')
    lines.append(f'**Sweet spot buffer length:** {d.get("sweet_spot_len", 0):.0f} chars')
    lines.append('')

    acc = d.get('accepted_patterns', [])
    if acc:
        lines.append('**Patterns that led to accepts:**')
        for a in acc[-8:]:
            lines.append(f'- "...{a}"')
        lines.append('')

    rej = d.get('rejected_patterns', [])
    if rej:
        lines.append('**Patterns that led to rejects:**')
        for r in rej[-8:]:
            lines.append(f'- "...{r}"')
        lines.append('')

    return '\n'.join(lines)


def render_emotions(p: dict) -> str:
    e = p.get('shards', {}).get('emotions', {})
    sd = e.get('state_distribution', e.get('state_dist', {}))
    if not sd:
        return ''
    lines = ['## Emotional Landscape', '']
    total = sum(sd.values())
    for state, count in sorted(sd.items(), key=lambda x: x[1], reverse=True):
        pct = count / total if total else 0
        lines.append(f'- **{state}**: {count} ({pct:.0%}) {_bar(pct, 20)}')
    lines.append('')

    lines.append(f'**Avg hesitation:** {e.get("avg_hesitation", 0):.3f}')
    lines.append('')

    frust = e.get('frustration_triggers', [])
    if frust:
        lines.append(f'**Frustration triggers:** {", ".join(frust[:5])}')
    flow = e.get('flow_triggers', [])
    if flow:
        lines.append(f'**Flow triggers:** {", ".join(flow[:5])}')
    lines.append('')

    trans = e.get('state_transitions', {})
    if trans:
        lines.append('**State transitions:**')
        for t, c in sorted(trans.items(), key=lambda x: x[1], reverse=True)[:8]:
            lines.append(f'- {t}: {c}x')
        lines.append('')

    return '\n'.join(lines)


def render_code_style(p: dict) -> str:
    cs = p.get('shards', {}).get('code_style', {})
    if not cs.get('top_imports'):
        return ''
    lines = ['## Code Style', '']
    lines.append(f'| Trait | Value |')
    lines.append(f'|-------|-------|')
    lines.append(f'| Quotes | {cs.get("preferred_quotes", "?")} |')
    lines.append(f'| Type hints | {cs.get("uses_type_hints", False)} |')
    lines.append(f'| Import style | {cs.get("import_style", "?")} |')
    lines.append(f'| Naming | {cs.get("naming_convention", "?")} |')
    lines.append(f'| Avg func length | {cs.get("avg_func_length", 0):.1f} lines |')
    lines.append(f'| Docstring rate | {cs.get("docstring_rate", 0):.0%} |')
    lines.append(f'| F-string rate | {cs.get("fstring_rate", 0):.0%} |')
    lines.append(f'| List comp rate | {cs.get("list_comp_rate", 0):.0%} |')
    lines.append('')

    imports = cs.get('top_imports', [])
    if imports:
        lines.append(f'**Top imports:** {", ".join(imports[:10])}')
    exceptions = cs.get('top_exceptions', [])
    if exceptions:
        lines.append(f'**Exception handling:** {", ".join(exceptions[:5])}')
    lines.append('')
    return '\n'.join(lines)


def render_predictions(p: dict) -> str:
    pr = p.get('shards', {}).get('predictions', {})
    lines = ['## Prediction Engine', '']
    wt = pr.get('working_templates', [])
    if wt:
        lines.append('**Working templates (accepted patterns):**')
        for t in wt[-5:]:
            lines.append(f'- {t}')
        lines.append('')
    dead = pr.get('dead_templates', [])
    if dead:
        lines.append('**Dead templates (always rejected):**')
        for t in dead[-5:]:
            lines.append(f'- {t}')
        lines.append('')
    phrases = pr.get('operator_phrases', [])
    if phrases:
        lines.append('**Operator phrases:** ' + ', '.join(f'"{ph}"' for ph in phrases[:8]))
        lines.append('')
    if not wt and not dead and not phrases:
        lines.append('*No prediction data accumulated yet.*')
        lines.append('')
    return '\n'.join(lines)


# ── SECTIONS (CIA SHARD) ──

def render_sections(p: dict) -> str:
    sections = p.get('shards', {}).get('sections', {})
    if not sections:
        return '## Sections\n\n*No section data yet. Restart thought completer to activate section tracking.*\n\n'
    lines = ['## Behavioral Sections (CIA Dossier)', '']
    for name, sec in sorted(sections.items(), key=lambda x: x[1].get('visit_count', 0), reverse=True):
        if not isinstance(sec, dict):
            continue
        v = sec.get('visit_count', 0)
        if v == 0:
            continue
        lines.append(f'### {name.upper()} ({v} visits)')
        lines.append('')

        # vitals
        lines.append(f'**Cognitive vitals:** WPM={sec.get("avg_wpm", 0):.1f} '
                      f'| Del={sec.get("avg_del_ratio", 0):.1%} '
                      f'| Hes={sec.get("avg_hesitation", 0):.3f} '
                      f'| Peak WPM={sec.get("peak_wpm", 0):.0f}')

        # emotional fingerprint
        dom = sec.get('dominant_state', 'unknown')
        sd = sec.get('state_dist', {})
        if sd:
            state_str = ', '.join(f'{s}={c}' for s, c in sorted(sd.items(), key=lambda x: x[1], reverse=True)[:4])
            lines.append(f'**Emotional fingerprint:** dominant={dom} | {state_str}')

        # entry/exit
        entry = sec.get('entry_states', [])
        exit_ = sec.get('exit_states', [])
        if entry:
            lines.append(f'**Entry states:** {" → ".join(entry[-5:])}')
        if exit_:
            lines.append(f'**Exit states:** {" → ".join(exit_[-5:])}')

        # suppression map
        supp = sec.get('suppressed_words', {})
        if supp:
            top_supp = _top_items(supp, 8)
            lines.append(f'**Suppressed words:** {", ".join(f"`{w}`({c}x)" for w, c in top_supp)}')
        rewrites = sec.get('rewrite_chains', [])
        if rewrites:
            lines.append(f'**Rewrite chains:** {len(rewrites)} recorded')
        abandons = sec.get('abandon_count', 0)
        if abandons:
            lines.append(f'**Abandoned messages:** {abandons}')

        # module heat
        hot = sec.get('hot_modules', {})
        if hot:
            top_hot = _top_items(hot, 6)
            lines.append(f'**Hot modules:** {", ".join(f"`{m}`({c})" for m, c in top_hot)}')

        # vocab
        iw = sec.get('intent_words', {})
        if iw:
            top_iw = _top_items(iw, 8)
            lines.append(f'**Vocabulary:** {", ".join(f"{w}({c})" for w, c in top_iw)}')

        # temporal
        hd = sec.get('hour_dist', {})
        if hd:
            top_hours = sorted(hd.items(), key=lambda x: int(x[1]), reverse=True)[:3]
            lines.append(f'**Peak hours (UTC):** {", ".join(f"{h}:00({c})" for h, c in top_hours)}')
        lines.append(f'**Avg session depth:** {sec.get("session_depth_avg", 0):.1f}')

        # completion style
        acc_len = sec.get('avg_accepted_len', 0)
        rej_len = sec.get('avg_rejected_len', 0)
        if acc_len or rej_len:
            lines.append(f'**Completion style:** accepted avg {acc_len:.0f} chars, '
                          f'rejected avg {rej_len:.0f} chars, '
                          f'code/prose ratio {sec.get("code_vs_prose_ratio", 0):.0%}')

        # question patterns
        qp = sec.get('question_patterns', [])
        if qp:
            lines.append('**Question patterns:**')
            for q in qp[-4:]:
                lines.append(f'  - "{q}"')

        # contradiction
        if sec.get('contradiction_count', 0) > 0:
            lines.append(f'**Contradictions:** {sec["contradiction_count"]} '
                          f'(lying index: {sec.get("lying_index", 0):.2f})')

        lines.append('')

    return '\n'.join(lines)


# ── INTELLIGENCE FILE ──

def render_intelligence(p: dict) -> str:
    intel = p.get('shards', {}).get('intelligence', {})
    secrets = intel.get('secrets', [])
    model = intel.get('operator_model', {})
    laws = intel.get('behavioral_laws', [])
    contradictions = intel.get('contradictions', [])

    lines = ['## Intelligence File', '']

    if not secrets and not any(model.values()):
        lines.append('*No secrets discovered yet. The system needs section data to deduce intelligence.*')
        lines.append('*Restart thought completer to activate the intelligence engine.*')
        lines.append('')
        return '\n'.join(lines)

    # operator model
    if any(model.values()):
        lines.append('### Operator Model')
        lines.append('')
        lines.append('| Trait | Deduction |')
        lines.append('|-------|-----------|')
        for k, v in model.items():
            if v is not None and v != [] and v != 0 and v != 1.0:
                display = ', '.join(v) if isinstance(v, list) else str(v)
                lines.append(f'| {k.replace("_", " ").title()} | {display} |')
        lines.append('')

    # secrets
    if secrets:
        lines.append(f'### Secrets ({len(secrets)} discovered)')
        lines.append('')
        for s in sorted(secrets, key=lambda x: x.get('confidence', 0), reverse=True):
            conf = s.get('confidence', 0)
            emoji = '🔴' if conf >= 0.8 else '🟡' if conf >= 0.6 else '⚪'
            lines.append(f'{emoji} **[{s.get("type", "?")}]** (conf={conf:.0%}) — '
                          f'{s.get("text", "")}')
            lines.append(f'  *evidence: {s.get("evidence", "?")} · discovered {s.get("discovered", "?")[:10]}*')
            lines.append('')

    # behavioral laws
    if laws:
        lines.append('### Behavioral Laws')
        lines.append('')
        for law in laws:
            lines.append(f'- **{law.get("law", "")}** (conf={law.get("confidence", 0):.0%}, '
                          f'evidence: {law.get("evidence", "")})')
        lines.append('')

    # contradictions
    if contradictions:
        lines.append('### Contradictions (Says vs Does)')
        lines.append('')
        for c in contradictions:
            lines.append(f'- **{c.get("section", "?")}**: talks about '
                          f'{", ".join(c.get("stated", [])[:3])} but never acts on them')
        lines.append('')

    return '\n'.join(lines)


# ── COMPLETION GRADES ──

def render_grades(p: dict) -> str:
    """Render completion grading data."""
    summary_path = ROOT / 'logs' / 'completion_grade_summary.json'
    grades_path = ROOT / 'logs' / 'completion_grades.jsonl'

    lines = ['## Completion Grades', '']

    if not grades_path.exists():
        lines.append('*No grades recorded yet. Restart thought completer to activate grading.*')
        lines.append('')
        return '\n'.join(lines)

    # Load summary
    summary = None
    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text('utf-8', errors='ignore'))
        except Exception:
            pass

    # Load recent grades
    recent = []
    for line in grades_path.read_text('utf-8', errors='ignore').strip().splitlines()[-20:]:
        try:
            recent.append(json.loads(line))
        except Exception:
            continue

    if summary:
        a = summary.get('all_time', {})
        r50 = summary.get('recent_50', {})
        trend = summary.get('trend', {})
        lines.append(f'**Total graded:** {summary.get("total_graded", 0)}')
        lines.append('')
        lines.append('| Metric | All-Time | Recent 50 |')
        lines.append('|--------|----------|-----------|')
        lines.append(f'| Composite | {a.get("avg_composite", 0):.3f} | {r50.get("avg_composite", 0):.3f} |')
        lines.append(f'| Relevance | {a.get("avg_relevance", 0):.3f} | {r50.get("avg_relevance", 0):.3f} |')
        lines.append(f'| Novelty | {a.get("avg_novelty", 0):.3f} | {r50.get("avg_novelty", 0):.3f} |')
        lines.append(f'| Echo | {a.get("avg_echo", 0):.3f} | {r50.get("avg_echo", 0):.3f} |')
        lines.append(f'| Accept rate | {a.get("accept_rate", 0):.1%} | {r50.get("accept_rate", 0):.1%} |')
        lines.append('')
        lines.append(f'**Trend:** {trend.get("direction", "?")} (delta={trend.get("delta", 0):+.3f})')
        lines.append('')

        # Length profile
        lp = summary.get('length_profile', {})
        if lp.get('accepted_avg'):
            lines.append(f'**Accepted length:** avg={lp["accepted_avg"]:.0f} chars '
                          f'(rejected avg={lp.get("rejected_avg", 0):.0f})')
            ar = lp.get('accepted_range', [0, 0])
            lines.append(f'**Accepted range:** {ar[0]}-{ar[1]} chars')
            lines.append('')

        # Context effectiveness
        ce = summary.get('context_effectiveness', {})
        if ce:
            lines.append('**Context file effectiveness:**')
            lines.append('| File | Accept Rate | Samples |')
            lines.append('|------|-------------|---------|')
            for f, d in sorted(ce.items(), key=lambda x: x[1]['accept_rate'], reverse=True):
                lines.append(f'| `{f}` | {d["accept_rate"]:.0%} | {d["total"]} |')
            lines.append('')

    # Recent grades
    if recent:
        lines.append('### Recent Completions')
        lines.append('')
        lines.append('| Outcome | Composite | Rel | Novel | Echo | Len | Context |')
        lines.append('|---------|-----------|-----|-------|------|-----|---------|')
        for g in recent[-10:]:
            icon = {'rewarded': '\u2b50', 'accepted': '\u2713', 'dismissed': '\u2717',
                    'ignored': '\u00b7', 'superseded': '\u21bb'}.get(g['outcome'], '?')
            ctx = ','.join(g.get('context_files', [])[:2]) or '-'
            lines.append(
                f'| {icon} {g["outcome"]} | {g["composite"]:.2f} | '
                f'{g["relevance"]:.2f} | {g["novelty"]:.2f} | '
                f'{g["echo"]:.2f} | {g["comp_len"]} | {ctx} |'
            )
        lines.append('')

    return '\n'.join(lines)


# ── FULL REPORT ──

def render_full_report(p: dict) -> str:
    parts = [
        render_header(p),
        render_intelligence(p),
        render_grades(p),
        render_sections(p),
        render_voice(p),
        render_rhythm(p),
        render_deletions(p),
        render_topics(p),
        render_decisions(p),
        render_emotions(p),
        render_code_style(p),
        render_predictions(p),
    ]
    return '\n'.join(part for part in parts if part)


SHARD_MAP = {
    'voice': render_voice,
    'rhythm': render_rhythm,
    'deletions': render_deletions,
    'topics': render_topics,
    'decisions': render_decisions,
    'emotions': render_emotions,
    'code_style': render_code_style,
    'predictions': render_predictions,
    'sections': render_sections,
    'intelligence': render_intelligence,
    'grades': render_grades,
}


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Render operator intelligence report')
    parser.add_argument('-o', '--output', help='Write to file instead of stdout')
    parser.add_argument('--section', choices=list(SHARD_MAP.keys()),
                        help='Render only one shard')
    parser.add_argument('--secrets', action='store_true',
                        help='Show only intelligence file')
    args = parser.parse_args()

    p = load_profile()
    if not p:
        print('No profile data found.')
        sys.exit(1)

    if args.secrets:
        md = render_header(p) + render_intelligence(p)
    elif args.section:
        md = render_header(p) + SHARD_MAP[args.section](p)
    else:
        md = render_full_report(p)

    if args.output:
        Path(args.output).write_text(md, encoding='utf-8')
        print(f'Written to {args.output}')
    else:
        print(md)


if __name__ == '__main__':
    main()
