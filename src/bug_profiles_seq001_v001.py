"""bug_profiles_seq001_v001 — Generate and browse persistent bug profiles.

Reads pigeon_registry.json + self-fix reports + rework_log.json
to produce a full browsable markdown profile per bug demon.

Called from prompt_enricher or manually:
    py -c "from src.bug_profiles_seq001_v001_seq001_v001 import generate_profiles; generate_profiles(Path('.'))"
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations
import json
import re
from pathlib import Path
from datetime import datetime, timezone

BUG_LEGEND = {
    'hi': ('hardcoded_import', 'Hardcode Gremlin', 'Welds imports to exact paths — breaks on rename day.'),
    'de': ('dead_export', 'Dead Export Shade', 'Leaves dead functions standing so everyone thinks they matter.'),
    'dd': ('duplicate_docstring', 'Mirror Imp', 'Duplicates the same explanation until nobody remembers which copy was first.'),
    'hc': ('high_coupling', 'Coupling Leech', 'Braids modules together until one cut hurts five files.'),
    'oc': ('over_hard_cap', 'Overcap Maw', 'Swells files past the hard cap. Split before it eats context.'),
    'qn': ('query_noise', 'Noise Imp', 'Fogs the query stream until real intent fights to stay visible.'),
}

# Comedy narrative templates per bug type — forward-looking, diagnostic
BUG_STORIES = {
    'oc': (
        "came in wheezing at {tokens} tokens — that's {pct}% over the {cap}-token hard cap. "
        "Every push it gains weight. v{ver}, still unsplit. "
        "{split_urgency} "
        "The pigeon compiler can carve this into shards in one command. The question is: when."
    ),
    'de': (
        "has {dead_count} dead export(s) still standing at attention like they matter. "
        "Nobody imports them. Nobody calls them. They just… sit there, consuming mental space. "
        "Remove them or give them a job. Right now they're decoration."
    ),
    'hi': (
        "welded its imports to exact file paths — the kind that shatter the moment pigeon renames anything. "
        "Swap to glob-based dynamic import (`_load_pigeon_module` pattern) before the next rename cycle catches it."
    ),
    'hc': (
        "braided itself to {partners} so tightly that touching one means touching all {partner_count}. "
        "Extract the shared logic into a common module. Or accept the pain every time you edit."
    ),
    'dd': (
        "duplicated its own docstring until there are {dup_count} copies. "
        "Nobody remembers which explanation is the real one. Pick one, kill the rest."
    ),
    'qn': (
        "is fogging the query stream with noise. Real intent gets lost in the static. "
        "Clean the signal path or add explicit intent markers."
    ),
}

HARD_CAP_TOKENS = 2000  # 200 lines * ~10 tok/line

SPLIT_URGENCY = {
    5000: "This one's CODE RED — 2.5x the cap, actively eating context window.",
    3000: "Significant bloat. Every prompt that touches this file pays the tax.",
    2000: "Over the line but not emergency. Schedule a split this push cycle.",
}


def _urgency(tokens: int) -> str:
    for threshold, msg in sorted(SPLIT_URGENCY.items(), reverse=True):
        if tokens >= threshold:
            return msg
    return "Just barely over. Keep an eye on it."


def _load_registry(root: Path) -> list[dict]:
    reg_path = root / 'pigeon_registry.json'
    if not reg_path.exists():
        return []
    reg = json.loads(reg_path.read_text('utf-8'))
    return reg.get('files', []) if isinstance(reg, dict) else reg


def _load_self_fix_issues(root: Path, module_name: str) -> list[str]:
    """Find self-fix scanner issues mentioning this module."""
    reports_dir = root / 'docs' / 'self_fix'
    if not reports_dir.exists():
        return []
    sorted_reports = sorted(reports_dir.glob('*.md'), reverse=True)
    issues = []
    for report in sorted_reports[:3]:  # last 3 reports
        text = report.read_text('utf-8', errors='ignore')
        for line in text.split('\n'):
            if module_name in line and ('hardcoded' in line.lower() or 'dead' in line.lower()
                                         or 'overcap' in line.lower() or 'duplicate' in line.lower()):
                issues.append(f"[{report.stem}] {line.strip()[:120]}")
    return issues[:5]


def _load_rework_history(root: Path, module_name: str) -> list[dict]:
    """Find rework verdicts related to this module."""
    rework_path = root / 'rework_log.json'
    if not rework_path.exists():
        return []
    lines = rework_path.read_text('utf-8', errors='ignore').strip().splitlines()
    hits = []
    for l in lines[-100:]:  # last 100 entries
        try:
            entry = json.loads(l)
        except Exception:
            continue
        hint = entry.get('query_hint', '') or ''
        if module_name.lower() in hint.lower():
            hits.append(entry)
    return hits[-5:]


def _beta_in_filename(path: str) -> str:
    """Extract β bug codes from filename, or return empty string."""
    m = re.search(r'_β(\w+?)(?:_|\.py$|$)', Path(path).stem)
    return m.group(1) if m else ''


def generate_profiles(root: Path) -> Path:
    """Generate docs/BUG_PROFILES.md — the browsable bug profile page."""
    files = _load_registry(root)
    now = datetime.now(timezone.utc)

    # Collect all bugged modules
    bugged = []
    for f in files:
        bugs = f.get('bug_keys', [])
        if not bugs:
            continue
        bugged.append(f)

    # Group by bug type
    by_type: dict[str, list[dict]] = {}
    for f in bugged:
        for bk in f.get('bug_keys', []):
            by_type.setdefault(bk, []).append(f)

    # Sort each group by recurrence (descending)
    for bk in by_type:
        by_type[bk].sort(key=lambda x: -sum((x.get('bug_counts') or {}).values()))

    lines = [
        f'# Bug Profiles — The Rogues Gallery',
        f'',
        f'*Auto-generated {now.strftime("%Y-%m-%d %H:%M UTC")} · {len(bugged)} modules carrying bugs · {len(by_type)} species identified*',
        f'',
        f'> Every bug here is alive. They have names, habits, and a body count.',
        f'> This page tells you who they are, what they\'re doing to your codebase, and what to do about it.',
        f'',
    ]

    # Summary — narrative style, not tables
    lines.append('## The Lineup')
    lines.append('')
    for bk in sorted(by_type.keys()):
        label, demon, tagline = BUG_LEGEND.get(bk, (bk, bk, ''))
        total_recur = sum(sum((f.get('bug_counts') or {}).values()) for f in by_type[bk])
        count = len(by_type[bk])
        lines.append(f'**{demon}** (`{bk}`) — {count} module{"s" if count != 1 else ""}, {total_recur} total sightings. *{tagline}*')
        lines.append('')

    # β persistence check — still important but conversational
    lines.append('## Filename β Check')
    lines.append('')
    lines.append('The β suffix in a filename is the bug\'s brand. If it\'s missing, pigeon lost track.')
    lines.append('')
    persist_ok = 0
    persist_miss = 0
    for f in bugged:
        path = f.get('path', '')
        fname_beta = _beta_in_filename(path)
        expected = ''.join(sorted(set(f.get('bug_keys', []))))
        if fname_beta == expected:
            persist_ok += 1
        else:
            persist_miss += 1
            abbrev = f.get('abbrev', f.get('name', ''))
            lines.append(f'- `{abbrev}` — should be β{expected}, filename says β{fname_beta or "(nothing)"}. Pigeon needs to re-stamp this one.')
    if persist_miss == 0:
        lines.append(f'All {persist_ok} filenames carry their β correctly. No strays.')
    else:
        lines.append(f'')
        lines.append(f'{persist_ok}/{persist_ok + persist_miss} branded correctly. {persist_miss} missing — next rename cycle should catch them.')
    lines.append('')

    # Detailed profiles per bug type — NARRATIVE FORM
    for bk in sorted(by_type.keys()):
        label, demon, desc = BUG_LEGEND.get(bk, (bk, bk, ''))
        entries = by_type[bk]

        lines.append(f'---')
        lines.append(f'## {demon}')
        lines.append(f'')
        lines.append(f'*{desc}* — {len(entries)} known host{"s" if len(entries) != 1 else ""}.')
        lines.append(f'')

        for f in entries:
            abbrev = f.get('abbrev', '') or f.get('name', '')
            name = f.get('name', '')
            path = f.get('path', '')
            ver = f.get('ver', 0)
            tokens = f.get('tokens', 0)
            counts = f.get('bug_counts', {})
            recur = sum(counts.values())
            entities = f.get('bug_entities', {})
            last_change = f.get('last_change', '')
            fname_beta = _beta_in_filename(path)
            expected_beta = ''.join(sorted(set(f.get('bug_keys', []))))

            lines.append(f'### {abbrev}')
            lines.append(f'')

            entity = entities.get(bk, '')
            if entity:
                lines.append(f'*Demon name: {entity}*')
                lines.append(f'')

            # Build the story
            story_args = {
                'tokens': tokens,
                'cap': HARD_CAP_TOKENS,
                'pct': round((tokens - HARD_CAP_TOKENS) / HARD_CAP_TOKENS * 100) if bk == 'oc' else 0,
                'ver': ver,
                'split_urgency': _urgency(tokens) if bk == 'oc' else '',
                'dead_count': counts.get('de', 1),
                'partners': ', '.join(entities.get('hc_partners', ['(unknown)'])) if bk == 'hc' else '',
                'partner_count': len(entities.get('hc_partners', [])) if bk == 'hc' else 0,
                'dup_count': counts.get('dd', 1),
            }
            template = BUG_STORIES.get(bk, '{name} has a bug. Fix it.')
            try:
                story = template.format(**story_args)
            except (KeyError, ValueError):
                story = f'Carrying `{bk}` bug. {tokens} tokens, v{ver}.'

            lines.append(f'`{abbrev}` {story}')
            lines.append(f'')
            lines.append(f'Spotted {recur}x across {ver} versions. '
                         f'{"Last touched: " + last_change + ". " if last_change else ""}'
                         f'β in filename: {"yes" if fname_beta == expected_beta else "**MISSING**"}.')
            lines.append(f'')

            # Self-fix history — keep but make it conversational
            sf_issues = _load_self_fix_issues(root, name or abbrev)
            if sf_issues:
                lines.append(f'Self-fix scanner has been watching:')
                for issue in sf_issues:
                    lines.append(f'- {issue}')
                lines.append(f'')

            # Rework history
            rework = _load_rework_history(root, name or abbrev)
            if rework:
                lines.append(f'Rework history (what happened when someone tried to fix it):')
                for r in rework:
                    v = r.get('verdict', '?')
                    q = r.get('query_hint', '')[:60]
                    lines.append(f'- {v}: "{q}"')
                lines.append(f'')

        lines.append(f'')

    # Write the file
    output = root / 'docs' / 'BUG_PROFILES.md'
    output.write_text('\n'.join(lines), encoding='utf-8')

    # Also write the JSON for programmatic access
    profiles_json = {
        'generated': now.isoformat(),
        'total_bugged': len(bugged),
        'persistence': {'ok': persist_ok, 'missing': persist_miss},
        'by_type': {},
        'all_modules': {},
    }
    for bk, entries in by_type.items():
        label, demon, desc = BUG_LEGEND.get(bk, (bk, bk, ''))
        profiles_json['by_type'][bk] = {
            'label': label,
            'demon': demon,
            'description': desc,
            'count': len(entries),
            'modules': [f.get('abbrev', f.get('name', '')) for f in entries],
        }
    for f in bugged:
        key = f.get('abbrev', '') or f.get('name', '')
        profiles_json['all_modules'][key] = {
            'name': f.get('name', ''),
            'path': f.get('path', ''),
            'ver': f.get('ver', 0),
            'tokens': f.get('tokens', 0),
            'bug_keys': f.get('bug_keys', []),
            'bug_counts': f.get('bug_counts', {}),
            'bug_entities': f.get('bug_entities', {}),
            'last_bug_mark': f.get('last_bug_mark', ''),
            'last_change': f.get('last_change', ''),
            'dossier_score': f.get('dossier_score', 0),
            'beta_in_filename': _beta_in_filename(f.get('path', '')),
            'beta_expected': ''.join(sorted(set(f.get('bug_keys', [])))),
        }

    json_out = root / 'logs' / 'bug_profiles_seq001_v001.json'
    json_out.write_text(json.dumps(profiles_json, indent=2), encoding='utf-8')

    return output


if __name__ == '__main__':
    out = generate_profiles(Path('.'))
    print(f'Generated: {out}')
