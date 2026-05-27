"""self_fix_tracker_seq001_v001 — accuracy scoring across self-fix reports.

parses all docs/self_fix/ reports into threads.
tracks which bugs persist, which resolve, which are new.
scores fix success rate per push cycle.
outputs logs/self_fix_accuracy.json for copilot consumption.
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──

import json
import re
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter


def _parse_report(path: Path) -> dict:
    text = path.read_text('utf-8', errors='ignore')
    m = re.search(r'(\d{4}-\d{2}-\d{2})_([a-f0-9]+)_', path.name)
    date = m.group(1) if m else ''
    commit = m.group(2) if m else ''

    problems = []
    blocks = re.split(r'###\s+\d+\.', text)[1:]
    for block in blocks:
        lines = block.strip().splitlines()
        if not lines:
            continue
        header = lines[0].strip()
        sev_m = re.search(r'\[(\w+)\]', header)
        severity = sev_m.group(1) if sev_m else 'UNKNOWN'
        bug_type = header.split(']')[-1].strip() if ']' in header else header

        file_path = ''
        for l in lines[1:]:
            if '**File**' in l:
                file_path = l.split(':', 1)[-1].strip().strip('`')
                break

        # normalize file to base module name (strip seq/ver/date/lambda noise)
        stem = Path(file_path).stem if file_path else ''
        # pigeon format: name_sNNN_vNNN_dNNNN_... or name_seqNNN_...
        base = re.sub(r'_s\d{3,4}_v\d{3,4}_.*$', '', stem)
        base = re.sub(r'_seq\d+.*$', '', base)
        problems.append({
            'type': bug_type,
            'severity': severity,
            'file': file_path,
            'base': base,
        })

    return {'date': date, 'commit': commit, 'problems': problems}


def compute_accuracy(root: Path) -> dict:
    sf_dir = root / 'docs' / 'self_fix'
    if not sf_dir.exists():
        return {'error': 'no self_fix directory'}

    reports = sorted(sf_dir.glob('*.md'))
    if len(reports) < 2:
        return {'error': 'need at least 2 reports'}

    parsed = [_parse_report(r) for r in reports]

    # build thread history: (bug_type, base_module) -> list of report indices
    thread_history = {}
    for i, report in enumerate(parsed):
        seen = set()
        for p in report['problems']:
            key = (p['type'], p['base'])
            seen.add(key)
        for key in seen:
            thread_history.setdefault(key, []).append(i)

    total_reports = len(parsed)
    recent_window = min(10, total_reports)
    recent_start = total_reports - recent_window

    # classify each thread
    threads = []
    for (bug_type, base), appearances in thread_history.items():
        first = appearances[0]
        last = appearances[-1]
        count = len(appearances)
        persistence = count / total_reports

        # how many of the last N reports does this appear in?
        recent_count = sum(1 for i in appearances if i >= recent_start)
        recent_ratio = recent_count / recent_window if recent_window else 0

        if last == total_reports - 1:
            if recent_count == recent_window and count >= total_reports * 0.5:
                status = 'eternal'
            elif recent_ratio >= 0.7:
                status = 'chronic'
            else:
                status = 'active'
        else:
            gap = total_reports - 1 - last
            if gap >= 3:
                status = 'resolved'
            else:
                status = 'maybe_resolved'

        threads.append({
            'type': bug_type,
            'module': base,
            'appearances': count,
            'first_report': first,
            'last_report': last,
            'persistence': round(persistence, 3),
            'recent_ratio': round(recent_ratio, 3),
            'status': status,
        })

    # score per-push fix rate
    fixes_per_push = []
    for i in range(1, total_reports):
        prev_keys = set((p['type'], p['base']) for p in parsed[i - 1]['problems'])
        curr_keys = set((p['type'], p['base']) for p in parsed[i]['problems'])
        resolved = prev_keys - curr_keys
        introduced = curr_keys - prev_keys
        carried = prev_keys & curr_keys
        fixes_per_push.append({
            'report': i,
            'date': parsed[i]['date'],
            'commit': parsed[i]['commit'],
            'resolved': len(resolved),
            'introduced': len(introduced),
            'carried': len(carried),
            'fix_rate': round(len(resolved) / max(len(prev_keys), 1), 3),
        })

    # aggregate stats
    status_counts = Counter(t['status'] for t in threads)
    total_threads = len(threads)
    avg_fix_rate = (sum(f['fix_rate'] for f in fixes_per_push) /
                    max(len(fixes_per_push), 1))

    # top persistent (chronic + eternal)
    persistent = [t for t in threads if t['status'] in ('eternal', 'chronic')]
    persistent.sort(key=lambda x: -x['appearances'])

    # recently resolved
    resolved = [t for t in threads if t['status'] in ('resolved', 'maybe_resolved')]
    resolved.sort(key=lambda x: -x['last_report'])

    result = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'total_reports': total_reports,
        'total_threads': total_threads,
        'status_breakdown': dict(status_counts),
        'avg_fix_rate': round(avg_fix_rate, 3),
        'last_5_pushes': fixes_per_push[-5:],
        'persistent_top_10': persistent[:10],
        'recently_resolved': resolved[:10],
        'narrative': _build_narrative(status_counts, avg_fix_rate, persistent,
                                      resolved, fixes_per_push, total_reports),
    }

    out_path = root / 'logs' / 'self_fix_accuracy.json'
    out_path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


def _build_narrative(status_counts, avg_fix_rate, persistent, resolved,
                     fixes_per_push, total_reports) -> str:
    parts = []

    # fix rate story
    pct = round(avg_fix_rate * 100, 1)
    if pct < 5:
        parts.append(f"fix rate is {pct}% — almost nothing actually gets fixed between pushes. "
                      "the scanner screams into the void.")
    elif pct < 15:
        parts.append(f"fix rate is {pct}% — some things move but the bulk just sits there.")
    elif pct < 30:
        parts.append(f"fix rate is {pct}% — decent churn. bugs are dying and being born.")
    else:
        parts.append(f"fix rate is {pct}% — aggressive cleanup cycle. things are actually improving.")

    # eternal bugs
    eternal = status_counts.get('eternal', 0)
    chronic = status_counts.get('chronic', 0)
    if eternal + chronic > 0:
        parts.append(
            f"{eternal} eternal bugs (every single report) and {chronic} chronic "
            f"(70%+ of reports). these are the ones that need structural fixes, not patches."
        )

    # resolved wins
    res_count = status_counts.get('resolved', 0) + status_counts.get('maybe_resolved', 0)
    if res_count > 0:
        parts.append(f"{res_count} threads resolved across {total_reports} pushes. proof the loop works sometimes.")

    # trend
    if len(fixes_per_push) >= 3:
        recent = fixes_per_push[-3:]
        trend = sum(f['fix_rate'] for f in recent) / 3
        earlier = fixes_per_push[:3]
        early_avg = sum(f['fix_rate'] for f in earlier) / 3 if earlier else 0
        if trend > early_avg * 1.3:
            parts.append("trend is improving — recent pushes fix more than early ones.")
        elif trend < early_avg * 0.7:
            parts.append("trend is degrading — early pushes fixed more than recent ones.")
        else:
            parts.append("trend is flat — fix rate hasn't changed much.")

    return ' '.join(parts)


def build_narrative_block(root: Path) -> str:
    accuracy = compute_accuracy(root)
    if 'error' in accuracy:
        return ''

    narrative = accuracy.get('narrative', '')
    avg_rate = accuracy.get('avg_fix_rate', 0)
    total = accuracy.get('total_threads', 0)
    status = accuracy.get('status_breakdown', {})

    persistent = accuracy.get('persistent_top_10', [])
    resolved = accuracy.get('recently_resolved', [])

    lines = [
        '<!-- pigeon:bug-voices -->',
        '## Bug Voices',
        '',
        f'*{total} threads tracked across {accuracy.get("total_reports", 0)} pushes · '
        f'fix rate: {round(avg_rate * 100, 1)}%*',
        '',
        f'> {narrative}',
        '',
    ]

    # persistent bugs — narrative voice
    if persistent:
        lines.append('**the ones that never leave:**')
        lines.append('')
        for t in persistent[:7]:
            mod = t['module'] or '(unknown)'
            n = t['appearances']
            total_r = accuracy['total_reports']
            if t['status'] == 'eternal':
                voice = f'`{mod}` — [{t["type"]}] {n}/{total_r} reports. every. single. one. this is structural.'
            else:
                voice = f'`{mod}` — [{t["type"]}] {n}/{total_r} reports. chronic. it comes back like clockwork.'
            lines.append(f'- {voice}')
        lines.append('')

    # resolved — celebrate
    if resolved:
        lines.append('**recently killed:**')
        lines.append('')
        for t in resolved[:5]:
            mod = t['module'] or '(unknown)'
            lines.append(f'- `{mod}` [{t["type"]}] — gone since report #{t["last_report"]+1}. it stayed dead.')
        lines.append('')

    # last push delta
    last = accuracy.get('last_5_pushes', [])
    if last:
        latest = last[-1]
        lines.append(f'**last push ({latest["date"]} {latest["commit"][:7]}):** '
                      f'{latest["resolved"]} fixed, {latest["introduced"]} new, '
                      f'{latest["carried"]} carried forward')
        lines.append('')

    lines.append('<!-- /pigeon:bug-voices -->')
    return '\n'.join(lines)
