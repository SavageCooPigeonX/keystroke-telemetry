"""Template selector — routes live telemetry to focused .prompt.md Copilot templates.

Solves the 'dump truck' problem: instead of injecting ALL data into
copilot-instructions.md, heavy context is routed to focused templates
that the operator invokes via /debug, /build, or /review in chat.

Every template gets the shared signal block (deleted words, cognitive state,
hot modules, bug voices) plus its own domain-specific data.
"""

import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROMPTS_DIR = '.github/prompts'


# ── data loaders ──────────────────────────────

def _json(p):
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text('utf-8', errors='ignore'))
    except Exception:
        return None


def _jsonl_tail(p, n=20):
    if not p.exists():
        return []
    ll = p.read_text('utf-8', errors='ignore').strip().splitlines()[-n:]
    out = []
    for l in ll:
        try:
            out.append(json.loads(l))
        except Exception:
            pass
    return out


def _commits(root, n=5):
    try:
        r = subprocess.run(
            ['git', 'log', f'-{n}', '--pretty=format:%h %s'],
            capture_output=True, text=True, cwd=str(root), timeout=5,
        )
        return r.stdout.strip().splitlines()
    except Exception:
        return []


# ── signal extraction ─────────────────────────

def _deleted_words(comps):
    words, seen = [], set()
    for c in comps[-8:]:
        for w in c.get('intent_deleted_words', c.get('deleted_words', [])):
            word = w.get('word', w) if isinstance(w, dict) else str(w)
            if word and len(word) > 3 and word not in seen:
                words.append(word)
                seen.add(word)
    return words


def _rewrites_block(comps):
    """Extract rewrites from compositions — shows what operator typed then changed."""
    rewrites = []
    for c in comps[-6:]:
        for rw in c.get('rewrites', []):
            old = rw.get('old', '').strip()
            new = rw.get('new', '').strip()[:80]
            if old and new and len(old) > 3:
                rewrites.append(f'"{old}" → "{new}"')
    return rewrites


def _unsaid_threads(comps):
    """Extract intent-deleted words — thoughts operator started but killed."""
    threads = []
    seen = set()
    for c in comps[-8:]:
        for w in c.get('intent_deleted_words', []):
            word = w.get('word', '') if isinstance(w, dict) else str(w)
            if word and len(word) > 4 and word not in seen:
                threads.append(word)
                seen.add(word)
    return threads


def _voice_directives(root):
    """Extract voice style directives from copilot-instructions if present."""
    ci = root / '.github' / 'copilot-instructions.md'
    if not ci.exists():
        return []
    text = ci.read_text('utf-8', errors='ignore')
    m = re.search(r'Voice directives.*?\n(.*?)(?:\n\n|\n\*\*|<!-- /)', text, re.S)
    if not m:
        return []
    lines = []
    for line in m.group(1).strip().splitlines():
        line = line.strip().lstrip('- ')
        if line and len(line) > 10:
            lines.append(line)
    return lines[:4]


def _cognitive_line(snapshot):
    if not snapshot:
        return '`unknown` | WPM: ? | Del: ?%'
    lp = snapshot.get('latest_prompt', {})
    sig = snapshot.get('signals', {})
    state = lp.get('state', 'unknown')
    wpm = sig.get('wpm', 0)
    del_r = sig.get('deletion_ratio', 0)
    return f'`{state}` | WPM: {wpm:.0f} | Del: {del_r * 100:.0f}%'


def detect_mode(root):
    """Detect task mode from dossier + recent commits."""
    root = Path(root)
    dossier = _json(root / 'logs' / 'active_dossier.json')
    if dossier and dossier.get('focus_bugs'):
        return 'debug'
    msgs = ' '.join(_commits(root)).lower()
    if any(k in msgs for k in ('fix', 'bug', 'broken', 'error')):
        return 'debug'
    if any(k in msgs for k in ('feat', 'add', 'build', 'implement')):
        return 'build'
    if any(k in msgs for k in ('refactor', 'review', 'audit', 'clean')):
        return 'review'
    return 'build'


# ── shared signal block ──────────────────────

def _shared_signals(root):
    snapshot = _json(root / 'logs' / 'prompt_telemetry_latest.json')
    comps = _jsonl_tail(root / 'logs' / 'chat_compositions.jsonl', 8)
    deleted = _deleted_words(comps)
    rewrites = _rewrites_block(comps)
    unsaid = _unsaid_threads(comps)
    voice = _voice_directives(root)
    hot = (snapshot or {}).get('hot_modules', [])[:5]
    cog = _cognitive_line(snapshot)

    lines = [
        '## Live Signals',
        '',
        f'**Cognitive:** {cog}',
    ]
    if deleted:
        lines.append(f'**Deleted words:** {", ".join(deleted)}')
    if unsaid:
        lines.append(f'**Unsaid threads:** {", ".join(unsaid)}')
    if rewrites:
        lines.append(f'**Rewrites:** {"; ".join(rewrites[:4])}')
    if hot:
        hot_s = ', '.join(f'`{h["module"]}` (hes={h["hes"]:.2f})' for h in hot)
        lines.append(f'**Hot modules:** {hot_s}')

    reg = _json(root / 'pigeon_registry.json')
    if reg:
        bugged = [f for f in reg.get('files', []) if f.get('bug_keys')]
        bugged.sort(key=lambda f: sum((f.get('bug_counts') or {}).values()), reverse=True)
        if bugged:
            bl = [f'`{f["name"]}` ({"+".join(f["bug_keys"])})' for f in bugged[:4]]
            lines.append(f'**Active bugs:** {", ".join(bl)}')

    directives = (snapshot or {}).get('coaching_directives', [])
    if directives:
        lines.append(f'**Coaching:** {"; ".join(directives[:3])}')

    # Raw telemetry signal codes (intent, state, WPM baseline)
    if snapshot:
        sig = snapshot.get('signals', {})
        lp = snapshot.get('latest_prompt', {})
        rs = snapshot.get('running_summary', {})
        bl = rs.get('baselines', {})
        intent = lp.get('intent', 'unknown')
        state = lp.get('state', 'unknown')
        avg_wpm = bl.get('avg_wpm', 0)
        avg_del = bl.get('avg_del', 0)
        lines.append(
            f'**Codes:** intent=`{intent}` state=`{state}` '
            f'bl_wpm={avg_wpm:.0f} bl_del={avg_del*100:.0f}%'
        )

    if voice:
        lines.append(f'**Voice:** {"; ".join(voice[:2])}')

    return '\n'.join(lines)


# ── debug template ────────────────────────────

def _debug_body(root):
    lines = []
    # Known issues from latest self-fix report
    sf_dir = root / 'docs' / 'self_fix'
    if sf_dir.is_dir():
        reports = sorted(sf_dir.glob('*.md'))
        if reports:
            text = reports[-1].read_text('utf-8', errors='ignore')
            # Extract CRITICAL blocks: issue type + file
            blocks = re.findall(
                r'\[CRITICAL\]\s*(\S+)\n-\s*\*\*File\*\*:\s*(.+)',
                text,
            )
            if blocks:
                lines += ['## Known Issues (from self-fix scanner)', '']
                seen = set()
                for issue_type, filepath in blocks[:10]:
                    key = f'{issue_type}|{filepath.strip()}'
                    if key not in seen:
                        seen.add(key)
                        lines.append(f'- [CRITICAL] {issue_type} in `{filepath.strip()}`')
                lines.append('')

    # Fragile contracts from push narratives
    narr_dir = root / 'docs' / 'push_narratives'
    if narr_dir.is_dir():
        narrs = sorted(narr_dir.glob('*.md'))[-3:]
        contracts = []
        for n in narrs:
            text = n.read_text('utf-8', errors='ignore')
            for m in re.finditer(r'(?:fragile|contract|assumption|risk|break).*', text, re.I):
                line = m.group(0).strip()[:150]
                if line and line not in contracts:
                    contracts.append(line)
        if contracts:
            lines += ['## Fragile Contracts', '']
            lines += [f'- {c}' for c in contracts[:6]]
            lines.append('')

    # Codebase clots
    veins = _json(root / 'pigeon_brain' / 'context_veins.json')
    if veins:
        clots = veins.get('clots', [])
        if clots:
            lines += ['## Codebase Clots (dead/bloated)', '']
            for c in clots[:5]:
                if isinstance(c, dict):
                    name = c.get('module', '?')
                    signals = ', '.join(c.get('clot_signals', []))
                    lines.append(f'- `{name}`: {signals}')
                else:
                    lines.append(f'- `{c}`')
            lines.append('')

    # Overcap files
    reg = _json(root / 'pigeon_registry.json')
    if reg:
        overcap = [f for f in reg.get('files', []) if f.get('tokens', 0) > 2000]
        overcap.sort(key=lambda f: f.get('tokens', 0), reverse=True)
        if overcap:
            lines += ['## Overcap Files (split candidates)', '']
            lines += [f'- `{f["name"]}` ({f.get("tokens", 0)} tok)' for f in overcap[:8]]
            lines.append('')

    # Active dossier
    dossier = _json(root / 'logs' / 'active_dossier.json')
    if dossier and dossier.get('focus_modules'):
        lines += ['## Active Bug Dossier', '']
        lines.append(f'**Focus modules:** {", ".join(dossier["focus_modules"])}')
        if dossier.get('focus_bugs'):
            lines.append(f'**Focus bugs:** {", ".join(dossier["focus_bugs"])}')
        lines.append('')

    return '\n'.join(lines)


# ── build template ────────────────────────────

def _build_body(root):
    lines = []
    reg = _json(root / 'pigeon_registry.json')
    if reg:
        files = reg.get('files', [])
        # Compact folder summary with intent codes
        folders = {}
        for f in files:
            folder = str(Path(f.get('path', '')).parent).replace('\\', '/')
            if folder == '.':
                folder = 'root'
            folders.setdefault(folder, []).append(f)

        lines += ['## Module Map (compact)', '']
        for folder in sorted(folders):
            items = sorted(folders[folder], key=lambda x: x.get('seq', 0))
            tok_total = sum(f.get('tokens', 0) for f in items)
            tok_s = f'{tok_total / 1000:.1f}K' if tok_total >= 1000 else str(tok_total)
            bugged = sum(1 for f in items if f.get('bug_keys'))
            bug_s = f' · {bugged} bugged' if bugged else ''
            lines.append(f'**{folder}** ({len(items)} modules, {tok_s} tok{bug_s})')
        lines.append('')

    # File consciousness fears
    profiles = _json(root / 'file_profiles.json')
    if profiles and isinstance(profiles, dict):
        fears = {}
        for name, p in profiles.items():
            for f in (p.get('fears') or []):
                fears[f] = fears.get(f, 0) + 1
        if fears:
            lines += ['## Codebase Fears (from file consciousness)', '']
            for fear, count in sorted(fears.items(), key=lambda x: -x[1])[:8]:
                lines.append(f'- {fear} ({count} modules)')
            lines.append('')

    # High coupling warnings
    if profiles and isinstance(profiles, dict):
        couples = []
        for name, p in profiles.items():
            for partner in (p.get('slumber_partners') or []):
                pname = partner if isinstance(partner, str) else partner.get('name', '?')
                couples.append(f'`{name}` ↔ `{pname}`')
        if couples:
            lines += ['## High Coupling', '']
            lines += [f'- {c}' for c in couples[:6]]
            lines.append('')

    # Recent commits
    commits = _commits(root, 8)
    if commits:
        lines += ['## Recent Commits', '']
        lines += [f'- {c}' for c in commits]
        lines.append('')

    return '\n'.join(lines)


# ── review template ───────────────────────────

def _review_body(root):
    lines = []
    # Rework stats
    rework_raw = _json(root / 'rework_log.json')
    if rework_raw:
        entries = rework_raw if isinstance(rework_raw, list) else rework_raw.get('entries', [])
        total = len(entries)
        reworked = sum(1 for e in entries if isinstance(e, dict) and e.get('verdict') != 'ok')
        rate = (reworked / total * 100) if total else 0
        lines += ['## Rework Surface', '']
        lines.append(f'**Rate:** {rate:.0f}% ({reworked}/{total} needed rework)')
        lines.append('')

    # Mutation effectiveness
    scores = _json(root / 'logs' / 'mutation_scores.json')
    if scores and isinstance(scores, dict):
        sections = scores.get('sections', scores)
        if isinstance(sections, dict):
            lines += ['## Mutation Effectiveness', '']
            for section, data in list(sections.items())[:8]:
                if isinstance(data, dict):
                    s = data.get('score', data.get('avg_score', '?'))
                    lines.append(f'- `{section}`: score={s}')
            lines.append('')

    # Coaching from operator profile
    snapshot = _json(root / 'logs' / 'prompt_telemetry_latest.json')
    if snapshot:
        directives = snapshot.get('coaching_directives', [])
        if directives:
            lines += ['## Coaching Directives', '']
            lines += [f'- {d}' for d in directives]
            lines.append('')

    # Edit pair patterns
    pairs = _jsonl_tail(root / 'logs' / 'edit_pairs.jsonl', 15)
    if pairs:
        modules = Counter(p.get('module', '') for p in pairs if p.get('module'))
        if modules:
            lines += ['## Recent Edit Targets', '']
            for mod, count in modules.most_common(8):
                lines.append(f'- `{mod}` ({count} edits)')
            lines.append('')

    # Recent commits for review context
    commits = _commits(root, 10)
    if commits:
        lines += ['## Recent Work', '']
        lines += [f'- {c}' for c in commits]
        lines.append('')

    return '\n'.join(lines)


# ── hydration entry point ────────────────────

_TEMPLATES = [
    ('debug', _debug_body,
     'Debug-focused context: known issues, fragile contracts, clots, dossier'),
    ('build', _build_body,
     'Build-focused context: module map, file consciousness, coupling, commits'),
    ('review', _review_body,
     'Review-focused context: rework rate, mutation scores, edit patterns, coaching'),
]


def hydrate_templates(root):
    """Write all .prompt.md files with current live data. Returns mode + results."""
    root = Path(root)
    prompts = root / PROMPTS_DIR
    prompts.mkdir(parents=True, exist_ok=True)

    mode = detect_mode(root)
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    shared = _shared_signals(root)

    results = {}
    for name, builder, desc in _TEMPLATES:
        body = builder(root)
        rec = ' (RECOMMENDED)' if name == mode else ''
        content = (
            f'---\n'
            f'description: "{desc}"\n'
            f'---\n\n'
            f'# /{name}{rec}\n\n'
            f'*Hydrated {now} · detected mode: {mode}*\n\n'
            f'{shared}\n\n---\n\n'
            f'{body}'
        )
        path = prompts / f'{name}.prompt.md'
        path.write_text(content, encoding='utf-8')
        results[name] = len(content)

    return {'mode': mode, 'templates': results, 'ts': now}


# ── inject into copilot-instructions ─────────

ACTIVE_TEMPLATE_START = '<!-- pigeon:active-template -->'
ACTIVE_TEMPLATE_END = '<!-- /pigeon:active-template -->'


def inject_active_template(root):
    """Write the selected template body as a managed block in copilot-instructions.md.

    This ensures Copilot always sees the focused context without requiring
    the operator to manually invoke /debug, /build, or /review.
    """
    root = Path(root)
    cp = root / '.github' / 'copilot-instructions.md'
    if not cp.exists():
        return False

    mode = detect_mode(root)
    now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    shared = _shared_signals(root)

    builders = {'debug': _debug_body, 'build': _build_body, 'review': _review_body}
    builder = builders.get(mode, _debug_body)
    body = builder(root)

    block_lines = [
        ACTIVE_TEMPLATE_START,
        f'## Active Template: /{mode}',
        '',
        f'*Auto-selected {now} · mode: {mode}*',
        '',
        shared,
        '',
        '---',
        '',
        body,
        ACTIVE_TEMPLATE_END,
    ]
    block = '\n'.join(block_lines)

    text = cp.read_text(encoding='utf-8')
    pat = re.compile(
        re.escape(ACTIVE_TEMPLATE_START) + r'.*?' + re.escape(ACTIVE_TEMPLATE_END),
        re.DOTALL,
    )
    if pat.search(text):
        new_text = pat.sub(block, text)
    elif '<!-- /pigeon:hooks -->' in text:
        anchor = '<!-- /pigeon:hooks -->'
        new_text = text.replace(anchor, anchor + '\n' + block)
    elif '<!-- /pigeon:bug-voices -->' in text:
        anchor = '<!-- /pigeon:bug-voices -->'
        new_text = text.replace(anchor, anchor + '\n' + block)
    else:
        new_text = text.rstrip() + '\n\n' + block + '\n'

    if new_text != text:
        cp.write_text(new_text, encoding='utf-8')
    return True


if __name__ == '__main__':
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    r = hydrate_templates(root)
    print(json.dumps(r, indent=2))
    ok = inject_active_template(root)
    print(f'Injected active template: {ok}')
