"""codebase_vitals.py — Snapshot & trend codebase health metrics.

On each push: snapshot compliance, entropy, bugs, import health, module count.
Append to logs/codebase_vitals.jsonl for time-series trending.
Read by vitals_renderer.py to generate the brain stats dashboard.
"""

import ast
import json
import re
from datetime import datetime, timezone
from pathlib import Path

VITALS_LOG = 'logs/codebase_vitals.jsonl'
HARD_CAP = 200


def _count_lines(p: Path) -> int:
    try:
        return len(p.read_text('utf-8').splitlines())
    except Exception:
        return 0


def _count_py_files(root: Path) -> dict:
    """Count .py files by directory, excluding build/venv/cache."""
    skip = {'.venv', '__pycache__', '.git', 'node_modules', 'build', '.next'}
    counts = {'total': 0, 'src': 0, 'pigeon_compiler': 0, 'pigeon_brain': 0,
              'streaming_layer': 0, 'client': 0, 'root': 0}
    for f in root.rglob('*.py'):
        parts = f.relative_to(root).parts
        if any(p in skip for p in parts):
            continue
        counts['total'] += 1
        top = parts[0] if len(parts) > 1 else 'root'
        if top in counts:
            counts[top] += 1
    return counts


def _compliance_stats(root: Path) -> dict:
    """Check pigeon code compliance: files under/over hard cap."""
    skip = {'.venv', '__pycache__', '.git', 'node_modules', 'build', '.next'}
    under = 0
    over = 0
    over_files = []
    for f in sorted(root.rglob('*.py')):
        parts = f.relative_to(root).parts
        if any(p in skip for p in parts):
            continue
        lines = _count_lines(f)
        if lines > HARD_CAP:
            over += 1
            over_files.append((str(f.relative_to(root)), lines))
        else:
            under += 1
    total = under + over
    pct = round(under / total * 100, 1) if total else 0
    return {
        'compliant': under,
        'over_cap': over,
        'total': total,
        'compliance_pct': pct,
        'worst_offenders': sorted(over_files, key=lambda x: -x[1])[:10],
    }


def _bug_stats(root: Path) -> dict:
    """Extract bug counts from latest self-fix report."""
    sf_dir = root / 'docs' / 'self_fix'
    if not sf_dir.exists():
        return {'total': 0, 'critical': 0, 'by_type': {}}
    reports = sorted(sf_dir.glob('*.md'))
    if not reports:
        return {'total': 0, 'critical': 0, 'by_type': {}}
    latest = reports[-1]
    text = latest.read_text('utf-8', errors='ignore')
    # Parse "Problems Found: N"
    m = re.search(r'Problems Found:\s*(\d+)', text)
    total = int(m.group(1)) if m else 0
    # Count by type
    by_type = {}
    for m in re.finditer(r'\[(?:CRITICAL|HIGH|MEDIUM|LOW)\]\s+(\w+)', text):
        t = m.group(1)
        by_type[t] = by_type.get(t, 0) + 1
    critical = sum(1 for m in re.finditer(r'\[CRITICAL\]', text))
    return {'total': total, 'critical': critical, 'by_type': by_type}


def _entropy_stats(root: Path) -> dict:
    """Read current entropy map."""
    emap = root / 'logs' / 'entropy_map.json'
    if not emap.exists():
        return {'global_avg': 0, 'high_pct': 0, 'shed_count': 0, 'responses': 0}
    try:
        data = json.loads(emap.read_text('utf-8'))
        return {
            'global_avg': round(data.get('global_avg_entropy', 0), 4),
            'high_pct': round(data.get('high_entropy_pct', 0), 1),
            'shed_count': data.get('shed_blocks_found', 0),
            'responses': data.get('total_responses', 0),
        }
    except Exception:
        return {'global_avg': 0, 'high_pct': 0, 'shed_count': 0, 'responses': 0}


def _import_health(root: Path) -> dict:
    """Quick import health check — count broken __init__.py files."""
    broken = 0
    total = 0
    for init in root.joinpath('src').rglob('__init__.py'):
        if '__pycache__' in str(init):
            continue
        total += 1
        try:
            code = init.read_text('utf-8')
            if code.strip():
                ast.parse(code)
        except SyntaxError:
            broken += 1
    healthy = total - broken
    pct = round(healthy / total * 100, 1) if total else 100
    return {'healthy': healthy, 'broken': broken, 'total': total, 'health_pct': pct}


def _heat_stats(root: Path) -> dict:
    """Summarize cognitive heat from file_heat_map.json."""
    hm = root / 'file_heat_map.json'
    if not hm.exists():
        return {'modules_tracked': 0, 'avg_hes': 0, 'hot_count': 0}
    try:
        data = json.loads(hm.read_text('utf-8'))
        hes_vals = []
        for mod, info in data.items():
            samples = info.get('samples', [])
            if samples:
                avg = sum(s.get('hes', 0) for s in samples) / len(samples)
                hes_vals.append(avg)
        avg_hes = round(sum(hes_vals) / len(hes_vals), 3) if hes_vals else 0
        hot = sum(1 for h in hes_vals if h > 0.6)
        return {'modules_tracked': len(data), 'avg_hes': avg_hes, 'hot_count': hot}
    except Exception:
        return {'modules_tracked': 0, 'avg_hes': 0, 'hot_count': 0}


def _operator_stats(root: Path) -> dict:
    """Pull latest operator telemetry."""
    telem = root / 'logs' / 'prompt_telemetry_latest.json'
    if not telem.exists():
        return {}
    try:
        data = json.loads(telem.read_text('utf-8'))
        summary = data.get('running_summary', {})
        return {
            'total_prompts': summary.get('total_prompts', 0),
            'avg_wpm': round(summary.get('baselines', {}).get('avg_wpm', 0), 1),
            'avg_del': round(summary.get('baselines', {}).get('avg_del', 0), 3),
            'dominant_state': summary.get('dominant_state', 'unknown'),
        }
    except Exception:
        return {}


def snapshot_vitals(root: Path, commit_hash: str = '', commit_msg: str = '') -> dict:
    """Take a complete codebase health snapshot. Returns the snapshot dict."""
    root = Path(root)
    now = datetime.now(timezone.utc).isoformat()

    snap = {
        'ts': now,
        'commit': commit_hash[:8] if commit_hash else '',
        'commit_msg': commit_msg[:80] if commit_msg else '',
        'compliance': _compliance_stats(root),
        'bugs': _bug_stats(root),
        'entropy': _entropy_stats(root),
        'imports': _import_health(root),
        'heat': _heat_stats(root),
        'operator': _operator_stats(root),
        'files': _count_py_files(root),
    }
    return snap


def append_vitals(root: Path, snap: dict):
    """Append a snapshot to the vitals JSONL log."""
    root = Path(root)
    log = root / VITALS_LOG
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, 'a', encoding='utf-8') as f:
        f.write(json.dumps(snap, ensure_ascii=False) + '\n')


def load_vitals(root: Path) -> list[dict]:
    """Load all vitals snapshots."""
    log = Path(root) / VITALS_LOG
    if not log.exists():
        return []
    entries = []
    for line in log.read_text('utf-8').splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def record_vitals(root: Path, commit_hash: str = '', commit_msg: str = '') -> dict:
    """One-shot: snapshot + append. Returns the snapshot."""
    snap = snapshot_vitals(root, commit_hash, commit_msg)
    append_vitals(root, snap)
    return snap


if __name__ == '__main__':
    root = Path('.')
    snap = record_vitals(root)
    print(f"Vitals snapshot recorded:")
    print(f"  Compliance: {snap['compliance']['compliance_pct']}% "
          f"({snap['compliance']['compliant']}/{snap['compliance']['total']})")
    print(f"  Bugs: {snap['bugs']['total']} ({snap['bugs']['critical']} critical)")
    print(f"  Entropy: H={snap['entropy']['global_avg']} "
          f"({snap['entropy']['high_pct']}% high)")
    print(f"  Import health: {snap['imports']['health_pct']}%")
    print(f"  Heat: {snap['heat']['hot_count']} hot modules")
    print(f"  Files: {snap['files']['total']} .py files")
