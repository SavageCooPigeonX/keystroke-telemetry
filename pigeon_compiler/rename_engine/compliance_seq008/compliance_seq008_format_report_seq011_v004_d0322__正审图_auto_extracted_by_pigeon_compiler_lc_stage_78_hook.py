"""compliance_seq008_format_report_seq011_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 011 | VER: v004 | 31 lines | ~320 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: stage_78_hook
# LAST:   2026-03-22 @ 276af14
# SESSIONS: 3
# ──────────────────────────────────────────────
import re
from .compliance_seq008_constants_seq001_v001__正审图 import MAX_LINES

def format_report(audit: dict) -> str:
    """Format audit results as readable text."""
    lines = []
    lines.append(f'=== COMPLIANCE REPORT ===')
    lines.append(f'Total files: {audit["total"]}')
    lines.append(f'Compliant (≤{MAX_LINES} lines): {audit["compliant"]} '
                 f'({audit["compliance_pct"]}%)')
    lines.append(f'Oversize: {len(audit["oversize"])}')
    lines.append('')

    for entry in audit['oversize']:
        icon = {'OVER': '⚠️', 'WARN': '🔶', 'CRITICAL': '🔴'}
        lines.append(f'{icon.get(entry["status"], "?")} [{entry["status"]:>8}] '
                     f'{entry["lines"]:>5} lines  {entry["path"]}')
        for s in entry.get('splits', []):
            lines.append(f'          → split at L{s["line"]}: '
                         f'{s["reason"]} → {s["suggested_name"]}')

    return '\n'.join(lines)
