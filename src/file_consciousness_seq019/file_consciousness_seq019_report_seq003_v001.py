"""file_consciousness_seq019_report_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import re

def consciousness_report(root: Path, active_file: str | None = None) -> str:
    """Build markdown report for injection into copilot-instructions.md.

    If active_file given, focuses on that file's consciousness + partners.
    Otherwise gives a system-wide summary.
    """
    profiles = load_profiles(root)
    if not profiles:
        return ''

    if active_file:
        stem = re.sub(r'_seq\d+.*', '', Path(active_file).stem)
        p = profiles.get(stem)
        if not p:
            return ''
        lines = [
            '### File Consciousness',
            f'*Active: `{stem}` | {p["personality"]} (v{p["version"]}) '
            f'| {p["tokens"]} tokens | hes={p["avg_hes"]}*',
        ]
        if p['partners']:
            lines.append('\n**Top partners:**')
            for pt in p['partners'][:3]:
                lines.append(f'- `{pt["name"]}` ({pt["score"]}) — {pt["reason"]}')
        if p['fears']:
            lines.append('\n**This file fears:**')
            for f in p['fears'][:4]:
                lines.append(f'- {f}')
        return '\n'.join(lines)

    # System-wide: top drama modules + most-feared patterns
    drama = sorted(profiles.items(), key=lambda x: x[1].get('version', 0), reverse=True)[:5]
    feared = {}
    for _, p in profiles.items():
        for f in p.get('fears', []):
            feared[f] = feared.get(f, 0) + 1
    top_fears = sorted(feared.items(), key=lambda x: x[1], reverse=True)[:4]

    lines = ['### File Consciousness (System)', f'*{len(profiles)} modules profiled*']
    if drama:
        lines.append('\n**High-drama modules (most mutations):**')
        for name, p in drama:
            lines.append(f'- `{name}` v{p["version"]} ({p["personality"]}) — '
                         f'{len(p.get("partners", []))} partners')
    if top_fears:
        lines.append('\n**Most common fears across codebase:**')
        for fear, count in top_fears:
            lines.append(f'- {fear} ({count} modules)')
    return '\n'.join(lines)
