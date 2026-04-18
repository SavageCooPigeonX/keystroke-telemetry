"""追跑f_ruhe_s010_v005_d0403_册复审净助_λFX_βoc_format_report_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

def format_report(report: dict) -> str:
    """Human-readable report."""
    lines = ['=== PIGEON HEAL REPORT ===', '']
    stages = report.get('stages', {})

    if 'scan' in stages:
        s = stages['scan']
        lines.append(f'Scan: {s.get("total", 0)} files, '
                     f'{s.get("non_compliant", 0)} non-compliant')

    if 'rename' in stages:
        r = stages['rename']
        if r.get('dry_run'):
            lines.append('Rename: DRY RUN (use --execute to apply)')
        elif r.get('skipped'):
            lines.append('Rename: skipped (all compliant)')
        else:
            lines.append(f'Rename: {r.get("renamed", 0)} files renamed')

    if 'import_rewrite' in stages:
        lines.append(f'Imports: {stages["import_rewrite"]} lines rewritten')

    if 'validate' in stages:
        v = stages['validate']
        status = 'PASS' if v.get('valid') else f'FAIL ({v.get("broken", 0)} broken)'
        lines.append(f'Validate: {status}')

    if 'nametag_drift' in stages:
        nd = stages['nametag_drift']
        renamed = nd.get('renamed', 0)
        if nd.get('drifted', 0):
            lines.append(f'Nametag: {nd["drifted"]} drifted, {renamed} renamed')
        else:
            lines.append('Nametag: all descriptions current')

    if 'manifests' in stages:
        m = stages['manifests']
        lines.append(f'Manifests: {m.get("written", 0)}/{m.get("total_folders", 0)} written')

    if 'compliance' in stages:
        c = stages['compliance']
        lines.append(f'Compliance: {c.get("compliant", 0)}/{c.get("total", 0)} '
                     f'({c.get("pct", 0)}%) — {c.get("oversize", 0)} oversize')
        crits = c.get('critical', [])
        if crits:
            lines.append(f'Critical ({len(crits)}):')
            for p in crits[:10]:
                lines.append(f'  🔴 {p}')

    return '\n'.join(lines)
