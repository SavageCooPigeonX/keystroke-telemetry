"""Seed historical vitals from self-fix reports + git log.
Run once: py _seed_historical_vitals.py
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('.')
VITALS_LOG = ROOT / 'logs' / 'codebase_vitals.jsonl'
SELF_FIX_DIR = ROOT / 'docs' / 'self_fix'


def _parse_report(path: Path) -> dict:
    """Extract stats from a self-fix report."""
    text = path.read_text('utf-8', errors='ignore')

    m = re.search(r'Problems Found:\s*(\d+)', text)
    total = int(m.group(1)) if m else 0

    m = re.search(r'Scanned\s+(\d+)\s+modules', text)
    modules_scanned = int(m.group(1)) if m else 0

    critical = len(re.findall(r'\[CRITICAL\]', text))
    by_type = {}
    for m in re.finditer(r'\[(?:CRITICAL|HIGH|MEDIUM|LOW)\]\s+(\w+)', text):
        t = m.group(1)
        by_type[t] = by_type.get(t, 0) + 1

    return {
        'total': total,
        'critical': critical,
        'by_type': by_type,
        'modules_scanned': modules_scanned,
    }


def _parse_report_date(name: str) -> str | None:
    """Extract date from report filename like 2026-03-16_c8de77c_self_fix.md."""
    m = re.match(r'(\d{4}-\d{2}-\d{2})', name)
    return m.group(1) if m else None


def _parse_commit_from_name(name: str) -> str:
    """Extract commit hash from report filename."""
    m = re.match(r'\d{4}-\d{2}-\d{2}_([a-f0-9]+)_', name)
    return m.group(1) if m else ''


def _get_git_commits() -> dict[str, dict]:
    """Build commit map: hash -> {ts, msg}."""
    import subprocess
    result = subprocess.run(
        ['git', 'log', '--format=%h|%aI|%s', '--reverse'],
        capture_output=True, text=True, cwd=str(ROOT)
    )
    commits = {}
    for line in result.stdout.strip().splitlines():
        parts = line.split('|', 2)
        if len(parts) == 3:
            commits[parts[0]] = {'ts': parts[1], 'msg': parts[2]}
    return commits


def seed():
    """Seed historical vitals from self-fix reports."""
    reports = sorted(SELF_FIX_DIR.glob('*.md'))
    commits = _get_git_commits()

    entries = []

    for rpt in reports:
        date_str = _parse_report_date(rpt.name)
        commit_hash = _parse_commit_from_name(rpt.name)

        if not date_str:
            continue

        stats = _parse_report(rpt)

        # Try to get timestamp from commit, fall back to date
        ts = None
        if commit_hash and commit_hash in commits:
            ts = commits[commit_hash]['ts']
            msg = commits[commit_hash]['msg']
        else:
            # Find closest commit by date
            ts = f"{date_str}T12:00:00+00:00"
            msg = ''

        # Build a partial vitals snapshot (we don't have full data for history)
        snap = {
            'ts': ts,
            'commit': commit_hash[:8] if commit_hash else '',
            'commit_msg': msg[:80] if msg else f'self-fix report {date_str}',
            'source': 'historical_seed',
            'compliance': {
                'compliant': 0,
                'over_cap': stats['by_type'].get('over_hard_cap', 0),
                'total': stats['modules_scanned'],
                'compliance_pct': 0,
                'worst_offenders': [],
            },
            'bugs': {
                'total': stats['total'],
                'critical': stats['critical'],
                'by_type': stats['by_type'],
            },
            'entropy': {'global_avg': 0, 'high_pct': 0, 'shed_count': 0, 'responses': 0},
            'imports': {'healthy': 0, 'broken': 0, 'total': 0, 'health_pct': 0},
            'heat': {'modules_tracked': 0, 'avg_hes': 0, 'hot_count': 0},
            'operator': {},
            'files': {'total': stats['modules_scanned'], 'src': 0, 'pigeon_compiler': 0,
                      'pigeon_brain': 0, 'streaming_layer': 0, 'client': 0, 'root': 0},
        }

        # Estimate compliance from bug data
        if stats['modules_scanned'] > 0:
            hardcoded = stats['by_type'].get('hardcoded_import', 0)
            over_cap = stats['by_type'].get('over_hard_cap', 0)
            # Rough estimate: modules not flagged are compliant
            compliant = max(0, stats['modules_scanned'] - over_cap)
            snap['compliance']['compliant'] = compliant
            snap['compliance']['compliance_pct'] = round(
                compliant / stats['modules_scanned'] * 100, 1
            )

        entries.append(snap)

    # Sort by timestamp
    entries.sort(key=lambda e: e['ts'])

    # Clear existing and write
    VITALS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(VITALS_LOG, 'w', encoding='utf-8') as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + '\n')

    # Now append a fresh live snapshot at the end
    from src.codebase_vitals import record_vitals
    import subprocess
    result = subprocess.run(
        ['git', 'log', '--format=%h|%s', '-1'],
        capture_output=True, text=True, cwd=str(ROOT)
    )
    parts = result.stdout.strip().split('|', 1)
    h = parts[0] if parts else ''
    m = parts[1] if len(parts) > 1 else ''
    record_vitals(ROOT, h, m)

    total = len(entries) + 1  # + live snapshot
    print(f"Seeded {len(entries)} historical entries + 1 live snapshot = {total} total")


if __name__ == '__main__':
    seed()
