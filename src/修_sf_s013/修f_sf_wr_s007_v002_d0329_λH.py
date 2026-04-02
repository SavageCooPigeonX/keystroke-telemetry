"""self_fix_seq013_write_report_decomposed_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v002 | 62 lines | ~593 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: organism_health_system
# LAST:   2026-03-29 @ 1f4291d
# SESSIONS: 1
# ──────────────────────────────────────────────
from pathlib import Path
import os
import re

def write_self_fix_report(root: Path, report: dict, commit_hash: str = '') -> Path:
    """Write problem report to docs/self_fix/."""
    from datetime import datetime, timezone
    out_dir = root / 'docs' / 'self_fix'
    out_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    tag = f'_{commit_hash}' if commit_hash else ''
    out_path = out_dir / f'{today}{tag}_self_fix.md'

    lines = [
        f'# Self-Fix Report — {today} {commit_hash}',
        f'',
        f'Scanned {report["total_files_scanned"]} modules, '
        f'{report["import_graph_size"]} in import graph.',
        f'',
    ]

    problems = report['problems']
    if problems:
        lines.append(f'## Problems Found: {len(problems)}')
        lines.append('')
        for i, p in enumerate(problems, 1):
            sev = p.get('severity', '?').upper()
            lines.append(f'### {i}. [{sev}] {p["type"]}')
            if 'file' in p:
                lines.append(f'- **File**: {p["file"]}')
            if 'line' in p:
                lines.append(f'- **Line**: {p["line"]}')
            if 'function' in p:
                lines.append(f'- **Function**: `{p["function"]}()`')
            if 'import' in p:
                lines.append(f'- **Import**: `{p["import"]}`')
            if 'count' in p:
                lines.append(f'- **Count**: {p["count"]}')
            if 'fan_in' in p:
                lines.append(f'- **Fan-in**: {p["fan_in"]} dependents')
            lines.append(f'- **Fix**: {p["fix"]}')
            lines.append('')
    else:
        lines.append('## No problems found.')
        lines.append('')

    cross = report.get('cross_context', {})
    if cross:
        lines.append('## Cross-File Context (changed files)')
        lines.append('')
        for rel, ctx in cross.items():
            lines.append(f'### {rel}')
            if ctx['imports_from']:
                lines.append(f'- **Imports from**: {", ".join(ctx["imports_from"])}')
            if ctx['imported_by']:
                lines.append(f'- **Imported by**: {", ".join(ctx["imported_by"])}')
            lines.append('')

    out_path.write_text('\n'.join(lines), encoding='utf-8')
    return out_path
