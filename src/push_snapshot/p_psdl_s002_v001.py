"""push_snapshot_seq001_v001_data_loaders_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 158 lines | ~1,414 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json

def _load_registry(root: Path) -> dict:
    p = root / 'pigeon_registry.json'
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text('utf-8'))
        # Registry format: {'generated': ..., 'total': N, 'files': [list of dicts]}
        files = data.get('files', data) if isinstance(data, dict) else data
        if isinstance(files, list):
            # Exclude build/ artifacts — they're compressed copies, not source
            return {m.get('name', f'mod_{i}'): m for i, m in enumerate(files)
                    if isinstance(m, dict)
                    and not m.get('path', '').startswith('build/')}
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
