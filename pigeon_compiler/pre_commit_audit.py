"""pre_commit_audit.py — Git pre-commit pigeon compliance hook.

Runs automatically on `git commit`.  Checks every staged .py file:
  1. Pigeon naming — must match {name}_seq{NNN}_v{NNN}... pattern
  2. Version bump  — modified pigeon files must increment v{NNN}
  3. Line count    — files over PIGEON_MAX (200) are flagged
  4. Intent slug   — warns if _lc_{intent} is missing

Generates a compliance report appended to
  documentation/manifests/COMMIT_AUDIT_LOG.md

Exit 0 always (advisory, never blocks commits).
"""
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Thresholds ────────────────────────────────────────────────
PIGEON_MAX = 200
PIGEON_RECOMMENDED = 50

# ── Pigeon stem regex (mirrors registry_seq012) ──────────────
PIGEON_STEM_RE = re.compile(
    r'^(?P<name>.+)_seq(?P<seq>\d{3})_v(?P<ver>\d{3})'
    r'(?:_d(?P<date>\d{4}))?'
    r'(?:__(?P<slug>[a-z0-9_]+))?$'
)
LC_SEP = '_lc_'

# ── Excluded paths (mirrors pigeon_limits) ───────────────────
EXCLUDE_DIRS = frozenset({
    '_llm_tests_put_all_test_and_debug_scripts_here',
    '__pycache__', '.venv', 'node_modules',
    'static', 'templates', '.github',
    'audit_backups', 'json_uploads', 'documentation',
    'maif_propaganda', 'logs',
})
EXCLUDE_NAMES = frozenset({
    '__init__.py', 'conftest.py', 'app.py',
    'Procfile', 'requirements.txt',
})


def _run_git(*args: str) -> str:
    r = subprocess.run(
        ['git'] + list(args),
        capture_output=True, text=True, encoding='utf-8',
    )
    return r.stdout.strip()


def _is_excluded(path: str) -> bool:
    parts = Path(path).parts
    if Path(path).name in EXCLUDE_NAMES:
        return True
    for d in EXCLUDE_DIRS:
        if d in parts:
            return True
    if Path(path).name.startswith('_') and '/' not in path:
        return True  # root-level debug scripts
    return False


def _parse_stem(stem: str) -> dict | None:
    m = PIGEON_STEM_RE.match(stem)
    if not m:
        return None
    slug = m.group('slug') or ''
    desc, intent = '', ''
    if slug:
        if LC_SEP in slug:
            desc, intent = slug.split(LC_SEP, 1)
        else:
            desc = slug
    return {
        'name': m.group('name'),
        'seq': int(m.group('seq')),
        'ver': int(m.group('ver')),
        'date': m.group('date') or '',
        'desc': desc,
        'intent': intent,
    }


def _count_lines(path: str) -> int:
    try:
        return len(Path(path).read_text(encoding='utf-8').splitlines())
    except (OSError, UnicodeDecodeError):
        return 0


def _get_previous_version(path: str) -> int | None:
    """Check if a file existed in HEAD with a different version number."""
    head_files = _run_git('diff', '--cached', '--diff-filter=M', '--name-only')
    if path not in head_files.splitlines():
        return None  # new file, not modified
    blob = _run_git('show', f'HEAD:{path}')
    if not blob:
        return None
    # The file existed — parse version from the committed filename
    parsed = _parse_stem(Path(path).stem)
    if not parsed:
        return None
    # Since pigeon files get renamed on version bump, check if the same-name
    # file existed in HEAD.  If it did, the version wasn't bumped.
    return parsed['ver']


def _staged_files() -> list[dict]:
    """Get all staged .py files with their status (A=added, M=modified)."""
    raw = _run_git('diff', '--cached', '--name-status')
    files = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        parts = line.split('\t')
        if len(parts) < 2:
            continue
        status, path = parts[0][0], parts[-1]  # R100 has 3 cols
        if path.endswith('.py'):
            files.append({'status': status, 'path': path})
    return files


def run_audit() -> dict:
    """Main audit entry point.  Returns structured report."""
    now = datetime.now(timezone.utc)
    staged = _staged_files()

    commit_msg = ''
    msg_file = os.environ.get('GIT_COMMIT_MSG', '')
    if msg_file and Path(msg_file).exists():
        commit_msg = Path(msg_file).read_text(encoding='utf-8').strip()

    report = {
        'timestamp': now.isoformat(),
        'date': now.strftime('%Y-%m-%d %H:%M UTC'),
        'total_staged': len(staged),
        'pigeon_files': [],
        'non_pigeon_py': [],
        'excluded': [],
        'warnings': [],
        'line_counts': [],
    }

    for f in staged:
        path = f['path']
        status = f['status']

        if _is_excluded(path):
            report['excluded'].append(path)
            continue

        stem = Path(path).stem
        parsed = _parse_stem(stem)

        if not parsed:
            report['non_pigeon_py'].append(path)
            report['warnings'].append(
                f"⚠️  NON-PIGEON: {path} — not following naming convention"
            )
            continue

        lines = _count_lines(path)
        entry = {
            'path': path,
            'status': status,
            'ver': parsed['ver'],
            'name': parsed['name'],
            'seq': parsed['seq'],
            'lines': lines,
            'has_intent': bool(parsed['intent']),
            'desc': parsed['desc'],
            'intent': parsed['intent'],
        }
        report['pigeon_files'].append(entry)

        # Line count check
        if lines > PIGEON_MAX:
            icon = '🔴' if lines > 500 else '🟠' if lines > 300 else '⚠️'
            report['warnings'].append(
                f"{icon} OVERSIZE: {path} — {lines} lines (max {PIGEON_MAX})"
            )
        report['line_counts'].append({'path': path, 'lines': lines})

        # Version bump check (only for modified files, not new)
        if status == 'M':
            # File was modified in-place without rename = no version bump
            report['warnings'].append(
                f"🔖 NO VERSION BUMP: {path} — still v{parsed['ver']:03d}"
            )

        # Intent check
        if not parsed['intent']:
            report['warnings'].append(
                f"📝 NO INTENT: {path} — missing _lc_{{intent}} suffix"
            )

    return report


def format_report(report: dict) -> str:
    """Format audit report as Markdown."""
    lines = []
    lines.append(f"### Commit Audit — {report['date']}")
    lines.append('')
    lines.append(f"**Staged files:** {report['total_staged']} | "
                 f"**Pigeon:** {len(report['pigeon_files'])} | "
                 f"**Excluded:** {len(report['excluded'])} | "
                 f"**Non-pigeon .py:** {len(report['non_pigeon_py'])}")
    lines.append('')

    if report['pigeon_files']:
        lines.append('| File | Ver | Lines | Status | Intent |')
        lines.append('|------|-----|------:|--------|--------|')
        for pf in sorted(report['pigeon_files'], key=lambda x: x['path']):
            status_icon = '🆕' if pf['status'] == 'A' else '✏️'
            line_icon = '✅' if pf['lines'] <= PIGEON_MAX else '⚠️'
            intent = pf['intent'] or '_(none)_'
            name = Path(pf['path']).stem
            if len(name) > 50:
                name = name[:47] + '...'
            lines.append(
                f"| {name} | v{pf['ver']:03d} | "
                f"{pf['lines']} {line_icon} | {status_icon} | {intent} |"
            )
        lines.append('')

    if report['warnings']:
        lines.append('**Warnings:**')
        for w in report['warnings']:
            lines.append(f'- {w}')
        lines.append('')

    total_lines = sum(lc['lines'] for lc in report['line_counts'])
    lines.append(f"**Total pigeon lines:** {total_lines}")
    lines.append('')
    lines.append('---')
    lines.append('')
    return '\n'.join(lines)


def write_audit_log(report_md: str, root: Path = None):
    """Append audit report to COMMIT_AUDIT_LOG.md."""
    root = root or Path('.')
    log_dir = root / 'documentation' / 'manifests'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / 'COMMIT_AUDIT_LOG.md'

    if not log_file.exists():
        header = ("# COMMIT_AUDIT_LOG.md\n"
                  "> Per-commit pigeon compliance audit trail.\n"
                  "> Auto-generated by pigeon_compiler pre-commit hook.\n\n")
        log_file.write_text(header + report_md, encoding='utf-8')
    else:
        existing = log_file.read_text(encoding='utf-8')
        # Insert new report after the header (before first ### or at end)
        header_end = existing.find('\n### ')
        if header_end == -1:
            log_file.write_text(existing + report_md, encoding='utf-8')
        else:
            log_file.write_text(
                existing[:header_end + 1] + report_md + existing[header_end + 1:],
                encoding='utf-8',
            )


def print_summary(report: dict):
    """Print a concise terminal summary."""
    n_pigeon = len(report['pigeon_files'])
    n_warn = len(report['warnings'])
    total_lines = sum(lc['lines'] for lc in report['line_counts'])

    print(f"\n🐦 Pigeon Audit: {n_pigeon} pigeon files, "
          f"{total_lines} lines, {n_warn} warning(s)")

    if report['warnings']:
        for w in report['warnings']:
            print(f"   {w}")
    else:
        print("   ✅ All checks passed")
    print()


def main():
    report = run_audit()

    if not report['pigeon_files'] and not report['non_pigeon_py']:
        # Nothing to audit (only excluded files or non-py)
        sys.exit(0)

    print_summary(report)
    report_md = format_report(report)
    write_audit_log(report_md)

    # Always exit 0 — advisory only, never block commits
    sys.exit(0)


if __name__ == '__main__':
    main()
