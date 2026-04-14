"""f_he_s009_v005_d0401_改名册追跑_λA_heal_report_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 46 lines | ~377 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re

def heal_report_text(report: dict) -> str:
    """Format heal report as readable text."""
    lines = []
    ts = report.get('timestamp', '?')
    lines.append(f'=== HEAL REPORT | {ts} ===')
    lines.append('')

    changed = report.get('changed_files', [])
    lines.append(f'Changed files: {len(changed)}')
    for f in changed[:20]:
        lines.append(f'  {f}')
    if len(changed) > 20:
        lines.append(f'  ... +{len(changed) - 20} more')
    lines.append('')

    folders = report.get('affected_folders', [])
    lines.append(f'Affected folders: {len(folders)}')
    for f in folders:
        lines.append(f'  {f}/')
    lines.append('')

    manifests = report.get('manifests_updated', [])
    lines.append(f'Manifests updated: {len(manifests)}')
    lines.append('')

    traces = report.get('intent_traces', [])
    if traces:
        lines.append(f'Intent traces ({len(traces)}):')
        for t in traces:
            lines.append(f'  {t["file"]}: {t["intent"]}')
        lines.append('')

    comp = report.get('compliance', {})
    lines.append(f'Compliance: {comp.get("compliant", 0)}/{comp.get("total", 0)} '
                 f'({comp.get("pct", 0)}%)')
    crits = comp.get('critical', [])
    if crits:
        lines.append(f'Critical files ({len(crits)}):')
        for c in crits[:10]:
            lines.append(f'  🔴 {c}')
    lines.append('')

    return '\n'.join(lines)
