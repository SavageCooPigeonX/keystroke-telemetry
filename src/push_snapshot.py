"""push_snapshot.py — Codebase health snapshots + drift analysis per push.

Each push captures a full health snapshot: compliance, bugs, entropy, coupling,
file sizes, deaths, operator state, module count. Drift is computed as the delta
between consecutive snapshots. This turns pushes into a time-series of codebase
health — not just narrative, but numerical drift tracking.

Usage:
    from src.push_snapshot import capture_snapshot, compute_drift, get_snapshot_history

Storage:
    logs/push_snapshots/{commit_hash}.json   — per-push snapshot
    logs/push_snapshots/_latest.json         — symlink to most recent
    logs/push_drift.jsonl                    — append-only drift log
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SNAPSHOT_DIR = 'logs/push_snapshots'
DRIFT_LOG = 'logs/push_drift.jsonl'


# ── snapshot capture ──

def capture_snapshot(root: Path, commit_hash: str, intent: str,
                     changed_files: list[str]) -> dict:
    """Capture a full codebase health snapshot at this push.

    Reads all live data sources: registry, self-fix, heat map, deaths,
    operator profile, push cycle state, module state files.
    """
    ts = datetime.now(timezone.utc).isoformat()

    registry = _load_registry(root)
    self_fix = _load_self_fix_counts(root)
    heat = _load_heat_map(root)
    deaths = _load_deaths(root)
    operator = _load_operator_signal(root)
    cycle_state = _load_cycle_state(root)
    probe_state = _load_probe_state(root)
    file_stats = _compute_file_stats(root, registry)
    coupling = _compute_coupling(registry)

    snapshot = {
        'schema': 'push_snapshot/v1',
        'ts': ts,
        'commit': commit_hash,
        'intent': intent,
        'changed_files': len(changed_files),
        'changed_py': len([f for f in changed_files if f.endswith('.py')]),

        # Module census
        'modules': {
            'total': len(registry),
            'with_bugs': sum(1 for m in registry.values() if m.get('bug_keys')),
            'over_cap': self_fix.get('over_hard_cap', 0),
            'compliant': file_stats['compliant'],
            'compliance_pct': round(file_stats['compliant'] / max(len(registry), 1) * 100, 1),
        },

        # Bug surface
        'bugs': {
            'total': self_fix.get('total', 0),
            'hardcoded_import': self_fix.get('hardcoded_import', 0),
            'over_hard_cap': self_fix.get('over_hard_cap', 0),
            'dead_export': self_fix.get('dead_export', 0),
            'high_coupling': self_fix.get('high_coupling', 0),
            'other': self_fix.get('other', 0),
        },

        # File size distribution
        'file_stats': {
            'avg_tokens': file_stats['avg_tokens'],
            'median_tokens': file_stats['median_tokens'],
            'max_tokens': file_stats['max_tokens'],
            'total_tokens': file_stats['total_tokens'],
            'files_under_50': file_stats['under_50'],
            'files_50_200': file_stats['range_50_200'],
            'files_over_200': file_stats['over_200'],
        },

        # Coupling health
        'coupling': {
            'high_coupling_pairs': coupling['high_pairs'],
            'avg_coupling': coupling['avg_coupling'],
            'max_coupling': coupling['max_coupling'],
        },

        # Execution health
        'deaths': {
            'total': deaths['total'],
            'by_cause': deaths['by_cause'],
        },

        # Heat map (cognitive load)
        'heat': {
            'modules_tracked': heat['count'],
            'avg_hesitation': heat['avg_hes'],
            'hottest': heat['hottest'][:5],
        },

        # Operator state
        'operator': {
            'prompts_since_last_push': operator.get('prompt_count', 0),
            'avg_wpm': operator.get('avg_wpm', 0),
            'avg_deletion': operator.get('avg_deletion', 0),
            'dominant_state': operator.get('dominant_state', 'unknown'),
            'dominant_intent': operator.get('dominant_intent', 'unknown'),
        },

        # Push cycle meta
        'cycle': {
            'number': cycle_state.get('total_cycles', 0),
            'sync_score': cycle_state.get('last_sync_score', 0),
            'predictions': cycle_state.get('last_prediction_count', 0),
        },

        # Probe intelligence
        'probes': {
            'modules_probed': probe_state['modules_probed'],
            'total_conversations': probe_state['total_convos'],
            'total_intents_extracted': probe_state['total_intents'],
            'total_pain_points': probe_state['total_pain'],
            'avg_engagement': probe_state['avg_engagement'],
        },
    }

    # Persist
    _save_snapshot(root, commit_hash, snapshot)
    return snapshot


# ── drift computation ──

def compute_drift(root: Path, current: dict, previous: dict | None = None) -> dict:
    """Compute drift between two snapshots.

    If no previous snapshot given, loads the most recent one.
    Returns deltas for every metric — positive = grew, negative = shrank.
    """
    if previous is None:
        previous = _load_previous_snapshot(root, current.get('commit', ''))

    if not previous:
        return {'status': 'first_snapshot', 'drift': {}}

    drift = {}

    # Module drift
    drift['modules_delta'] = current['modules']['total'] - previous['modules']['total']
    drift['compliance_delta'] = round(
        current['modules']['compliance_pct'] - previous['modules']['compliance_pct'], 1)
    drift['over_cap_delta'] = current['modules']['over_cap'] - previous['modules']['over_cap']

    # Bug drift
    drift['bugs_delta'] = current['bugs']['total'] - previous['bugs']['total']
    drift['bugs_new'] = max(0, drift['bugs_delta'])
    drift['bugs_fixed'] = max(0, -drift['bugs_delta'])
    drift['hardcoded_import_delta'] = (
        current['bugs']['hardcoded_import'] - previous['bugs']['hardcoded_import'])

    # File size drift
    drift['avg_tokens_delta'] = round(
        current['file_stats']['avg_tokens'] - previous['file_stats']['avg_tokens'], 1)
    drift['total_tokens_delta'] = (
        current['file_stats']['total_tokens'] - previous['file_stats']['total_tokens'])
    drift['bloat_direction'] = (
        'bloating' if drift['avg_tokens_delta'] > 10
        else 'compressing' if drift['avg_tokens_delta'] < -10
        else 'stable')

    # Coupling drift
    drift['coupling_delta'] = round(
        current['coupling']['avg_coupling'] - previous['coupling']['avg_coupling'], 3)
    drift['high_coupling_delta'] = (
        current['coupling']['high_coupling_pairs'] - previous['coupling']['high_coupling_pairs'])

    # Death drift
    drift['deaths_delta'] = current['deaths']['total'] - previous['deaths']['total']

    # Heat drift
    drift['avg_hes_delta'] = round(
        current['heat']['avg_hesitation'] - previous['heat']['avg_hesitation'], 3)

    # Operator drift
    drift['wpm_delta'] = round(
        current['operator']['avg_wpm'] - previous['operator']['avg_wpm'], 1)
    drift['deletion_delta'] = round(
        current['operator']['avg_deletion'] - previous['operator']['avg_deletion'], 3)

    # Sync drift
    drift['sync_delta'] = round(
        current['cycle']['sync_score'] - previous['cycle']['sync_score'], 3)

    # Probe drift
    drift['probes_delta'] = (
        current['probes']['total_conversations'] - previous['probes']['total_conversations'])
    drift['intents_delta'] = (
        current['probes']['total_intents_extracted'] - previous['probes']['total_intents_extracted'])

    # Overall health score (0-100)
    drift['health_score'] = _compute_health_score(current)
    drift['prev_health_score'] = _compute_health_score(previous)
    drift['health_delta'] = round(drift['health_score'] - drift['prev_health_score'], 1)

    # Health direction
    if drift['health_delta'] > 2:
        drift['health_direction'] = 'improving'
    elif drift['health_delta'] < -2:
        drift['health_direction'] = 'degrading'
    else:
        drift['health_direction'] = 'stable'

    # Time between pushes
    try:
        t_cur = datetime.fromisoformat(current['ts'])
        t_prev = datetime.fromisoformat(previous['ts'])
        drift['hours_since_last_push'] = round((t_cur - t_prev).total_seconds() / 3600, 1)
    except Exception:
        drift['hours_since_last_push'] = None

    # Mutation summary (what changed most)
    drift['biggest_moves'] = _biggest_moves(drift)

    result = {
        'status': 'computed',
        'current_commit': current.get('commit', ''),
        'previous_commit': previous.get('commit', ''),
        'drift': drift,
    }

    # Persist to drift log
    _append_drift_log(root, result)
    return result


def get_snapshot_history(root: Path, limit: int = 10) -> list[dict]:
    """Load last N snapshots, most recent first."""
    snap_dir = root / SNAPSHOT_DIR
    if not snap_dir.exists():
        return []
    files = sorted(snap_dir.glob('*.json'), reverse=True)
    # Exclude _latest.json
    files = [f for f in files if f.stem != '_latest']
    result = []
    for f in files[:limit]:
        try:
            result.append(json.loads(f.read_text('utf-8')))
        except Exception:
            continue
    return result


# ── data loaders ──

def _load_registry(root: Path) -> dict:
    p = root / 'pigeon_registry.json'
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text('utf-8'))
        # Registry format: {'generated': ..., 'total': N, 'files': [list of dicts]}
        files = data.get('files', data) if isinstance(data, dict) else data
        if isinstance(files, list):
            return {m.get('name', f'mod_{i}'): m for i, m in enumerate(files)
                    if isinstance(m, dict)}
        if isinstance(files, dict):
            return {k: v for k, v in files.items() if isinstance(v, dict)}
        return {}
    except Exception:
        return {}


def _load_self_fix_counts(root: Path) -> dict:
    """Parse latest self-fix report for bug category counts."""
    sf_dir = root / 'docs' / 'self_fix'
    if not sf_dir.exists():
        return {'total': 0}
    files = sorted(sf_dir.glob('*.md'))
    if not files:
        return {'total': 0}
    latest = files[-1]
    text = latest.read_text('utf-8', errors='ignore')

    counts: dict[str, int] = {'total': 0, 'other': 0}
    categories = ['hardcoded_import', 'over_hard_cap', 'dead_export',
                   'high_coupling', 'duplicate_docstring', 'query_noise']
    for cat in categories:
        counts[cat] = 0

    import re
    # Count by scanning for category markers
    for cat in categories:
        matches = re.findall(rf'\b{cat}\b', text)
        counts[cat] = len(matches)
        counts['total'] += len(matches)

    # Try to extract total from "Problems Found: N" line
    m = re.search(r'Problems Found:\s*(\d+)', text)
    if m:
        counts['total'] = int(m.group(1))

    return counts


def _load_heat_map(root: Path) -> dict:
    p = root / 'file_heat_map.json'
    if not p.exists():
        return {'count': 0, 'avg_hes': 0, 'hottest': []}
    try:
        data = json.loads(p.read_text('utf-8'))
        modules = []
        for name, info in data.items():
            avg_hes = info.get('avg_hes', 0)
            if isinstance(info, dict) and 'samples' in info:
                samples = info['samples']
                if samples:
                    hes_vals = [s.get('hes', 0) for s in samples if isinstance(s, dict)]
                    avg_hes = sum(hes_vals) / len(hes_vals) if hes_vals else 0
            modules.append({'name': name, 'hes': round(avg_hes, 3)})
        modules.sort(key=lambda x: x['hes'], reverse=True)
        all_hes = [m['hes'] for m in modules if m['hes'] > 0]
        return {
            'count': len(modules),
            'avg_hes': round(sum(all_hes) / len(all_hes), 3) if all_hes else 0,
            'hottest': modules[:10],
        }
    except Exception:
        return {'count': 0, 'avg_hes': 0, 'hottest': []}


def _load_deaths(root: Path) -> dict:
    p = root / 'execution_death_log.json'
    if not p.exists():
        return {'total': 0, 'by_cause': {}}
    try:
        data = json.loads(p.read_text('utf-8'))
        if not isinstance(data, list):
            return {'total': 0, 'by_cause': {}}
        by_cause: dict[str, int] = {}
        for d in data:
            cause = d.get('cause', 'unknown')
            by_cause[cause] = by_cause.get(cause, 0) + 1
        return {'total': len(data), 'by_cause': by_cause}
    except Exception:
        return {'total': 0, 'by_cause': {}}


def _load_operator_signal(root: Path) -> dict:
    """Load latest operator signal from push cycle state or prompt telemetry."""
    p = root / 'logs' / 'prompt_telemetry_latest.json'
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text('utf-8'))
        summary = data.get('running_summary', {})
        latest = data.get('latest_prompt', {})
        return {
            'prompt_count': summary.get('total_prompts', 0),
            'avg_wpm': summary.get('avg_wpm', 0),
            'avg_deletion': summary.get('avg_del_ratio', 0),
            'dominant_state': summary.get('dominant_state', 'unknown'),
            'dominant_intent': latest.get('intent', 'unknown'),
        }
    except Exception:
        return {}


def _load_cycle_state(root: Path) -> dict:
    p = root / 'logs' / 'push_cycle_state.json'
    if p.exists():
        try:
            return json.loads(p.read_text('utf-8'))
        except Exception:
            pass
    return {}


def _load_probe_state(root: Path) -> dict:
    state_dir = root / 'logs' / 'module_state'
    if not state_dir.exists():
        return {'modules_probed': 0, 'total_convos': 0, 'total_intents': 0,
                'total_pain': 0, 'avg_engagement': 0}
    total_convos = 0
    total_intents = 0
    total_pain = 0
    engagement_sum = 0.0
    count = 0
    for f in state_dir.glob('*.json'):
        try:
            s = json.loads(f.read_text('utf-8'))
            convos = s.get('conversation_count', 0)
            if convos > 0:
                count += 1
                total_convos += convos
                total_intents += len(s.get('extracted_intents', []))
                total_pain += len(s.get('pain_points', []))
                engagement_sum += s.get('engagement_score', 0)
        except Exception:
            continue
    return {
        'modules_probed': count,
        'total_convos': total_convos,
        'total_intents': total_intents,
        'total_pain': total_pain,
        'avg_engagement': round(engagement_sum / max(count, 1), 3),
    }


def _compute_file_stats(root: Path, registry: dict) -> dict:
    tokens = [m.get('tokens', 0) for m in registry.values() if isinstance(m, dict)]
    if not tokens:
        return {'avg_tokens': 0, 'median_tokens': 0, 'max_tokens': 0,
                'total_tokens': 0, 'under_50': 0, 'range_50_200': 0,
                'over_200': 0, 'compliant': 0}
    tokens.sort()
    median = tokens[len(tokens) // 2]
    return {
        'avg_tokens': round(sum(tokens) / len(tokens), 1),
        'median_tokens': median,
        'max_tokens': max(tokens),
        'total_tokens': sum(tokens),
        'under_50': sum(1 for t in tokens if t <= 50),
        'range_50_200': sum(1 for t in tokens if 50 < t <= 200),
        'over_200': sum(1 for t in tokens if t > 200),
        'compliant': sum(1 for t in tokens if t <= 200),
    }


def _compute_coupling(registry: dict) -> dict:
    """Extract coupling stats from registry bug_keys."""
    high_pairs = 0
    coupling_scores = []
    for m in registry.values():
        if not isinstance(m, dict):
            continue
        bugs = m.get('bug_keys', [])
        if 'high_coupling' in bugs:
            high_pairs += 1
        bc = m.get('bug_counts', {})
        if bc.get('high_coupling', 0) > 0:
            coupling_scores.append(bc['high_coupling'])
    avg = sum(coupling_scores) / len(coupling_scores) if coupling_scores else 0
    return {
        'high_pairs': high_pairs,
        'avg_coupling': round(avg, 3),
        'max_coupling': max(coupling_scores, default=0),
    }


# ── health scoring ──

def _compute_health_score(snapshot: dict) -> float:
    """Compute an overall health score (0-100) from snapshot metrics.

    Weighted composite — higher = healthier codebase.
    """
    score = 50.0  # baseline

    # Compliance (+25 max)
    compliance = snapshot.get('modules', {}).get('compliance_pct', 0)
    score += (compliance / 100) * 25

    # Bug penalty (-20 max)
    total_bugs = snapshot.get('bugs', {}).get('total', 0)
    total_modules = max(snapshot.get('modules', {}).get('total', 1), 1)
    bug_ratio = min(total_bugs / total_modules, 1.0)
    score -= bug_ratio * 20

    # File size bonus (+10 max) — reward small files
    avg_tokens = snapshot.get('file_stats', {}).get('avg_tokens', 500)
    if avg_tokens <= 50:
        score += 10
    elif avg_tokens <= 200:
        score += 5
    elif avg_tokens > 500:
        score -= 5

    # Death penalty (-5 max)
    deaths = snapshot.get('deaths', {}).get('total', 0)
    score -= min(deaths * 0.5, 5)

    # Sync bonus (+10 max)
    sync = snapshot.get('cycle', {}).get('sync_score', 0)
    score += sync * 10

    # Probe engagement bonus (+5 max)
    probed = snapshot.get('probes', {}).get('modules_probed', 0)
    if probed > 10:
        score += 5
    elif probed > 0:
        score += 2

    # Heat penalty (-5 max) — high average hesitation = cognitive debt
    avg_hes = snapshot.get('heat', {}).get('avg_hesitation', 0)
    if avg_hes > 0.6:
        score -= 5
    elif avg_hes > 0.4:
        score -= 2

    return round(max(0, min(100, score)), 1)


# ── persistence ──

def _save_snapshot(root: Path, commit_hash: str, snapshot: dict):
    snap_dir = root / SNAPSHOT_DIR
    snap_dir.mkdir(parents=True, exist_ok=True)

    # Save by commit hash
    snap_path = snap_dir / f'{commit_hash}.json'
    snap_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), 'utf-8')

    # Update _latest.json
    latest_path = snap_dir / '_latest.json'
    latest_path.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), 'utf-8')


def _load_previous_snapshot(root: Path, current_commit: str) -> dict | None:
    """Load the snapshot before the current one."""
    snap_dir = root / SNAPSHOT_DIR
    if not snap_dir.exists():
        return None
    files = sorted(snap_dir.glob('*.json'))
    files = [f for f in files if f.stem not in ('_latest', current_commit)]
    if not files:
        return None
    try:
        return json.loads(files[-1].read_text('utf-8'))
    except Exception:
        return None


def _append_drift_log(root: Path, drift_result: dict):
    log_path = root / DRIFT_LOG
    log_path.parent.mkdir(parents=True, exist_ok=True)
    drift_result['ts'] = datetime.now(timezone.utc).isoformat()
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(drift_result) + '\n')


def _biggest_moves(drift: dict) -> list[str]:
    """Identify the biggest drift metrics for narrative generation."""
    moves = []
    if abs(drift.get('compliance_delta', 0)) > 2:
        d = drift['compliance_delta']
        moves.append(f"compliance {'up' if d > 0 else 'down'} {abs(d):.1f}%")
    if abs(drift.get('bugs_delta', 0)) > 5:
        d = drift['bugs_delta']
        moves.append(f"bugs {'up' if d > 0 else 'down'} {abs(d)}")
    if abs(drift.get('avg_tokens_delta', 0)) > 20:
        d = drift['avg_tokens_delta']
        moves.append(f"avg file size {'grew' if d > 0 else 'shrank'} {abs(d):.0f} tokens")
    if abs(drift.get('health_delta', 0)) > 3:
        d = drift['health_delta']
        moves.append(f"health {'up' if d > 0 else 'down'} {abs(d):.1f} pts")
    if drift.get('deaths_delta', 0) > 0:
        moves.append(f"{drift['deaths_delta']} new execution deaths")
    if drift.get('intents_delta', 0) > 0:
        moves.append(f"{drift['intents_delta']} new operator intents extracted")
    if drift.get('probes_delta', 0) > 0:
        moves.append(f"{drift['probes_delta']} new probe conversations")
    if not moves:
        moves.append('no significant drift')
    return moves


# ── injection into copilot prompt ──

BLOCK_START = '<!-- pigeon:push-drift -->'
BLOCK_END = '<!-- /pigeon:push-drift -->'


def inject_drift_block(root: Path, snapshot: dict, drift_result: dict):
    """Inject the latest drift analysis into copilot-instructions.md."""
    ci_path = root / '.github' / 'copilot-instructions.md'
    if not ci_path.exists():
        return

    d = drift_result.get('drift', {})
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

    lines = [BLOCK_START]
    lines.append('## Push Drift Analysis')
    lines.append('')
    lines.append(f'*Snapshot at `{snapshot.get("commit", "?")}` · {ts}*')
    lines.append('')

    # Health headline
    health = d.get('health_score', 0)
    direction = d.get('health_direction', 'stable')
    prev = d.get('prev_health_score')
    if prev is not None:
        lines.append(f'**Health: {health}/100** ({direction}, was {prev})')
    else:
        lines.append(f'**Health: {health}/100** (first snapshot)')
    lines.append('')

    # Key deltas
    if d.get('biggest_moves'):
        lines.append('**Biggest moves:**')
        for move in d['biggest_moves']:
            lines.append(f'- {move}')
        lines.append('')

    # Numbers
    m = snapshot.get('modules', {})
    b = snapshot.get('bugs', {})
    f = snapshot.get('file_stats', {})
    lines.append(f'**Modules:** {m.get("total", 0)} ({m.get("compliance_pct", 0)}% compliant)')
    lines.append(f'**Bugs:** {b.get("total", 0)} (hi={b.get("hardcoded_import", 0)} oc={b.get("over_hard_cap", 0)})')
    lines.append(f'**Avg tokens/file:** {f.get("avg_tokens", 0)} ({d.get("bloat_direction", "unknown")})')
    lines.append(f'**Deaths:** {snapshot.get("deaths", {}).get("total", 0)}')
    lines.append(f'**Sync:** {snapshot.get("cycle", {}).get("sync_score", 0)}')
    lines.append(f'**Probes:** {snapshot.get("probes", {}).get("modules_probed", 0)} modules, {snapshot.get("probes", {}).get("total_intents_extracted", 0)} intents')
    lines.append('')

    # Hours since last push
    hrs = d.get('hours_since_last_push')
    if hrs:
        lines.append(f'*{hrs}h since last push*')
        lines.append('')

    lines.append(BLOCK_END)
    block = '\n'.join(lines)

    content = ci_path.read_text('utf-8')
    start_idx = content.find(BLOCK_START)
    end_idx = content.find(BLOCK_END)

    if start_idx != -1 and end_idx != -1:
        content = content[:start_idx] + block + content[end_idx + len(BLOCK_END):]
    else:
        # Insert before predictions block
        marker = '<!-- pigeon:predictions -->'
        idx = content.find(marker)
        if idx == -1:
            marker = '<!-- pigeon:operator-state -->'
            idx = content.find(marker)
        if idx >= 0:
            content = content[:idx] + block + '\n' + content[idx:]
        else:
            content += '\n\n' + block

    ci_path.write_text(content, 'utf-8')
