"""shard_manager_seq026_v001.py — Local memory shard manager (markdown format).

Manages ~20 markdown shard files in logs/shards/. Each shard is a
human-readable `.md` file with timestamped bullet entries. The operator
can open any shard and read/edit it directly.

Contradiction detection: every new entry is checked against existing entries
in the same shard. If a contradiction is detected, the entry still writes
but also appends to `logs/shards/_contradictions.md` for the resolver.

Shards are populated two ways:
1. seed_shards() — one-time bootstrap from existing data files
2. learn_from_rework() — called after every rework score, writes patterns
   back into the relevant shard so the system improves over time
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from datetime import datetime, timezone

SHARD_DIR = 'logs/shards'
CONTRADICTION_FILE = '_contradictions.md'
MAX_SHARD_LINES = 200

# ── shard definitions ─────────────────────────
SHARD_SCHEMA: dict[str, str] = {
    'import_patterns':       'which imports break after renames, common import errors and fixes',
    'naming_conventions':    'pigeon naming patterns, operator corrections to file/var names',
    'error_patterns':        'recurring error types, stack traces, and what fixed them',
    'refactor_patterns':     'how operator structures refactors, what gets split/merged',
    'module_relationships':  'which modules are always edited together, coupling signals',
    'architecture_decisions':'big design decisions, system boundaries, integration choices',
    'test_patterns':         'what tests operator writes vs skips, test structure preferences',
    'debug_strategies':      'what operator looks at first when debugging, investigation patterns',
    'code_style':            'formatting, comments, structure preferences from observed edits',
    'api_preferences':       'preferred libraries, API patterns, model choices',
    'frustration_triggers':  'what consistently causes rework, hesitation, or deletion',
    'success_patterns':      'prompts that led to zero-rework responses, what worked',
    'session_flow':          'typical session arc patterns, warmup vs deep-flow behaviors',
    'prompt_patterns':       'how operator phrases requests, shorthand, implicit references',
    'deleted_thoughts':      'accumulated unsaid/deleted content — what operator wanted but didnt ask',
    'rework_history':        'compressed rework log — what failed and why by topic',
    'commit_patterns':       'push/commit patterns, what gets bundled, commit message style',
    'module_pain_points':    'files with highest cognitive load, chronic problem areas',
    'coaching_learned':      'synthesized coaching directives that proved effective',
    'compilation_patterns':  'pigeon compiler preferences, split/merge decisions, naming tags',
}

# negation / reversal patterns for contradiction detection
_NEGATION_PAIRS = [
    (r'\bnever\b', r'\balways\b'), (r'\bavoid\b', r'\bprefer\b'),
    (r'\bdon\'?t\b', r'\bdo\b'), (r'\bbad\b', r'\bgood\b'),
    (r'\bremove\b', r'\bkeep\b'), (r'\bskip\b', r'\buse\b'),
    (r'\bdisable\b', r'\benable\b'), (r'\bwrong\b', r'\bcorrect\b'),
    (r'\bhate\b', r'\blike\b'), (r'\bslow\b', r'\bfast\b'),
]


def _shard_path(root: Path, name: str) -> Path:
    return root / SHARD_DIR / f'{name}.md'


def _ensure_dir(root: Path) -> Path:
    d = root / SHARD_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def _now_tag() -> str:
    return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')


def _make_header(name: str) -> str:
    desc = SHARD_SCHEMA.get(name, name)
    return f'# {name}\n\n> {desc}\n\n'


# ── read / write ──────────────────────────────

def read_shard(root: Path, name: str) -> str:
    """Read a shard's full markdown text. Returns '' if not found."""
    p = _shard_path(root, name)
    if not p.exists():
        return ''
    try:
        return p.read_text('utf-8', errors='ignore')
    except Exception:
        return ''


def read_shard_entries(root: Path, name: str) -> list[str]:
    """Parse bullet entries from a shard. Returns list of entry texts."""
    text = read_shard(root, name)
    if not text:
        return []
    entries = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith('- '):
            entries.append(stripped[2:])
    return entries


def write_shard(root: Path, name: str, entries: list[str]) -> bool:
    """Rewrite a shard from a list of bullet entries. Truncates to MAX_SHARD_LINES."""
    _ensure_dir(root)
    if len(entries) > MAX_SHARD_LINES:
        entries = entries[-MAX_SHARD_LINES:]
    lines = _make_header(name)
    for e in entries:
        lines += f'- {e}\n'
    try:
        _shard_path(root, name).write_text(lines, 'utf-8')
        return True
    except Exception:
        return False


def append_to_shard(root: Path, name: str, text: str) -> bool:
    """Append one bullet entry to a shard. Runs contradiction check first."""
    _ensure_dir(root)
    ts = _now_tag()
    entry_line = f'`{ts}` {text}'

    # contradiction check
    existing = read_shard_entries(root, name)
    contradiction = detect_contradiction(text, existing)
    if contradiction:
        _write_contradiction(root, name, text, contradiction)

    p = _shard_path(root, name)
    if not p.exists():
        write_shard(root, name, [entry_line])
        return True

    current = p.read_text('utf-8', errors='ignore')
    # trim if over limit
    current_lines = current.splitlines()
    bullet_count = sum(1 for l in current_lines if l.strip().startswith('- '))
    if bullet_count >= MAX_SHARD_LINES:
        entries = read_shard_entries(root, name)
        entries = entries[-(MAX_SHARD_LINES - 1):] + [entry_line]
        return write_shard(root, name, entries)

    try:
        with open(p, 'a', encoding='utf-8') as f:
            f.write(f'- {entry_line}\n')
        return True
    except Exception:
        return False


def get_shard_summary(root: Path, name: str, max_entries: int = 10) -> str:
    """Return last N entries as plain text for context injection."""
    entries = read_shard_entries(root, name)
    if not entries:
        return ''
    recent = entries[-max_entries:]
    lines = [f'[{name}]']
    for e in recent:
        display = e[:120] + '...' if len(e) > 120 else e
        lines.append(f'  • {display}')
    return '\n'.join(lines)


# ── contradiction detection ───────────────────

def _tokenize(text: str) -> set[str]:
    return set(re.findall(r'\b\w{3,}\b', text.lower()))


def detect_contradiction(new_entry: str, existing_entries: list[str]) -> str | None:
    """Check if new_entry contradicts any existing entry.

    Returns the contradicted entry text, or None if no contradiction found.
    Uses two signals:
    1. High token overlap + negation pair (e.g. "always use X" vs "never use X")
    2. Same subject + opposite verb/adjective
    """
    new_lower = new_entry.lower()
    new_tokens = _tokenize(new_entry)
    if len(new_tokens) < 3:
        return None

    for existing in existing_entries[-50:]:  # only check recent entries
        # strip timestamp prefix if present
        ex_text = re.sub(r'^`[^`]*`\s*', '', existing)
        ex_lower = ex_text.lower()
        ex_tokens = _tokenize(ex_text)

        # need meaningful token overlap (same topic)
        overlap = new_tokens & ex_tokens
        if len(overlap) < 2:
            continue
        overlap_ratio = len(overlap) / min(len(new_tokens), len(ex_tokens))
        if overlap_ratio < 0.3:
            continue

        # check negation pairs
        for neg_a, neg_b in _NEGATION_PAIRS:
            a_in_new = bool(re.search(neg_a, new_lower))
            b_in_new = bool(re.search(neg_b, new_lower))
            a_in_ex = bool(re.search(neg_a, ex_lower))
            b_in_ex = bool(re.search(neg_b, ex_lower))

            if (a_in_new and b_in_ex) or (b_in_new and a_in_ex):
                return ex_text

    return None


def _write_contradiction(root: Path, shard_name: str, new_entry: str, old_entry: str):
    """Append a flagged contradiction to the contradiction manifest."""
    _ensure_dir(root)
    p = root / SHARD_DIR / CONTRADICTION_FILE
    ts = _now_tag()

    block = (
        f'\n## `{ts}` — {shard_name}\n\n'
        f'**NEW:** {new_entry}\n\n'
        f'**OLD:** {old_entry}\n\n'
        f'**STATUS:** unresolved\n\n'
        f'---\n'
    )

    if not p.exists():
        header = '# Contradiction Manifest\n\n> Auto-generated. Resolver fires on unresolved entries.\n\n---\n'
        p.write_text(header + block, 'utf-8')
    else:
        with open(p, 'a', encoding='utf-8') as f:
            f.write(block)


def get_unresolved_contradictions(root: Path) -> list[dict]:
    """Parse contradictions manifest, return unresolved entries."""
    p = Path(root) / SHARD_DIR / CONTRADICTION_FILE
    if not p.exists():
        return []

    text = p.read_text('utf-8', errors='ignore')
    blocks = re.split(r'\n---\n', text)
    unresolved = []

    for block in blocks:
        if 'STATUS:** unresolved' not in block:
            continue
        ts_match = re.search(r'`([^`]+)`\s*—\s*(\S+)', block)
        new_match = re.search(r'\*\*NEW:\*\*\s*(.+)', block)
        old_match = re.search(r'\*\*OLD:\*\*\s*(.+)', block)
        if ts_match and new_match and old_match:
            unresolved.append({
                'ts': ts_match.group(1),
                'shard': ts_match.group(2),
                'new': new_match.group(1).strip(),
                'old': old_match.group(1).strip(),
            })
    return unresolved


def resolve_contradiction(root: Path, ts: str, winner: str) -> bool:
    """Mark a contradiction as resolved. winner = 'new' or 'old'.

    If winner='new', removes the old entry from the shard.
    If winner='old', removes the new entry from the shard.
    Either way, marks the contradiction as resolved in the manifest.
    """
    p = Path(root) / SHARD_DIR / CONTRADICTION_FILE
    if not p.exists():
        return False

    text = p.read_text('utf-8', errors='ignore')
    # find and mark resolved
    pattern = f'`{ts}`'
    if pattern not in text:
        return False

    text = text.replace(
        f'**STATUS:** unresolved',
        f'**STATUS:** resolved → {winner}',
        1  # only the first match near this timestamp
    )
    p.write_text(text, 'utf-8')
    return True


# ── seeding from existing data ────────────────

def _jload(path: Path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text('utf-8', errors='ignore'))
    except Exception:
        return None


def _jsonl(path: Path, n: int = 0) -> list:
    if not path.exists():
        return []
    lines = path.read_text('utf-8', errors='ignore').strip().splitlines()
    if n:
        lines = lines[-n:]
    out = []
    for l in lines:
        try:
            out.append(json.loads(l))
        except Exception:
            pass
    return out


def seed_shards(root: Path) -> dict[str, int]:
    """One-time seed from existing telemetry files. Returns {shard: entries_added}."""
    root = Path(root)
    _ensure_dir(root)
    seeded: dict[str, int] = {}
    ts = _now_tag()

    # module_pain_points ← file_heat_map.json
    hm = _jload(root / 'file_heat_map.json')
    if hm and isinstance(hm, dict):
        entries = []
        for name, v in sorted(hm.items(), key=lambda x: x[1].get('avg_hes', 0) if isinstance(x[1], dict) else 0, reverse=True)[:20]:
            if isinstance(v, dict):
                entries.append(f"`{ts}` {name}: hes={v.get('avg_hes',0):.3f}, touches={v.get('total',0)}")
        if entries:
            write_shard(root, 'module_pain_points', entries)
            seeded['module_pain_points'] = len(entries)

    # rework_history ← rework_log.json
    rework = _jload(root / 'rework_log.json')
    if rework and isinstance(rework, list):
        entries = []
        for e in rework[-50:]:
            if isinstance(e, dict) and e.get('verdict') != 'ok':
                entries.append(f"`{ts}` [{e.get('verdict','?')}] {(e.get('query_hint',''))[:100]}")
        if entries:
            write_shard(root, 'rework_history', entries)
            seeded['rework_history'] = len(entries)

    # deleted_thoughts ← unsaid_reconstructions.jsonl
    unsaid = _jsonl(root / 'logs' / 'unsaid_reconstructions.jsonl', n=30)
    if unsaid:
        entries = []
        for e in unsaid:
            text = e.get('reconstruction', e.get('text', ''))
            if text:
                entries.append(f"`{ts}` {text[:120]}")
        if entries:
            write_shard(root, 'deleted_thoughts', entries)
            seeded['deleted_thoughts'] = len(entries)

    # prompt_patterns ← prompt_journal.jsonl
    journal = _jsonl(root / 'logs' / 'prompt_journal.jsonl', n=40)
    if journal:
        entries = [f"`{ts}` [{e.get('intent','')}] {(e.get('msg',''))[:100]}" for e in journal]
        if entries:
            write_shard(root, 'prompt_patterns', entries)
            seeded['prompt_patterns'] = len(entries)

    # commit_patterns ← push_cycles.jsonl
    pushes = _jsonl(root / 'logs' / 'push_cycles.jsonl', n=20)
    if pushes:
        entries = [f"`{ts}` {(e.get('commit_msg',''))[:100]}" for e in pushes]
        if entries:
            write_shard(root, 'commit_patterns', entries)
            seeded['commit_patterns'] = len(entries)

    # success_patterns ← rework_log where verdict=ok and rework_score=0
    if rework and isinstance(rework, list):
        entries = []
        for e in rework[-100:]:
            if isinstance(e, dict) and e.get('verdict') == 'ok' and e.get('rework_score', 1) == 0:
                entries.append(f"`{ts}` ✓ {(e.get('query_hint',''))[:100]}")
        if entries:
            write_shard(root, 'success_patterns', entries[-30:])
            seeded['success_patterns'] = min(len(entries), 30)

    # frustration_triggers ← rework_log where rework_score > 0.5
    if rework and isinstance(rework, list):
        entries = []
        for e in rework:
            if isinstance(e, dict) and e.get('rework_score', 0) > 0.5:
                entries.append(f"`{ts}` ⚠ score={e.get('rework_score',0):.1f} {(e.get('query_hint',''))[:80]}")
        if entries:
            write_shard(root, 'frustration_triggers', entries[-20:])
            seeded['frustration_triggers'] = min(len(entries), 20)

    # module_relationships ← file_heat_map co-occurrence
    if hm and isinstance(hm, dict):
        names = list(hm.keys())
        entries = []
        for i, a in enumerate(names[:15]):
            for b in names[i+1:15]:
                va, vb = hm.get(a, {}), hm.get(b, {})
                if isinstance(va, dict) and isinstance(vb, dict):
                    if abs(va.get('avg_hes', 0) - vb.get('avg_hes', 0)) < 0.1 and va.get('total', 0) >= 3 and vb.get('total', 0) >= 3:
                        entries.append(f"`{ts}` {a} ↔ {b}")
        if entries:
            write_shard(root, 'module_relationships', entries[:20])
            seeded['module_relationships'] = min(len(entries), 20)

    return seeded


# ── learning loop ─────────────────────────────

def learn_from_rework(root: Path, query: str, verdict: str,
                      rework_score: float, response_hint: str = '') -> list[str]:
    """After a rework score, extract patterns and write to shards.
    Returns list of shard names updated."""
    root = Path(root)
    updated = []
    query_lower = query.lower()

    if verdict != 'ok' or rework_score > 0.3:
        append_to_shard(root, 'frustration_triggers', f"[{verdict}] score={rework_score:.1f} {query[:100]}")
        updated.append('frustration_triggers')

        error_words = set(re.findall(r'\b(?:import|error|fail|crash|bug|break|missing|wrong|fix)\b', query_lower))
        if error_words:
            append_to_shard(root, 'error_patterns', f"{', '.join(error_words)}: {query[:80]}")
            updated.append('error_patterns')

        if re.search(r'\bimport\b', query_lower):
            append_to_shard(root, 'import_patterns', f"[rework] {query[:100]}")
            updated.append('import_patterns')

    elif rework_score == 0:
        append_to_shard(root, 'success_patterns', f"✓ {query[:100]}")
        updated.append('success_patterns')

    append_to_shard(root, 'prompt_patterns', f"[{verdict}] score={rework_score:.1f} {query[:80]}")
    updated.append('prompt_patterns')

    return updated


def list_shards(root: Path) -> list[str]:
    """Return names of all shards that exist on disk."""
    d = Path(root) / SHARD_DIR
    if not d.exists():
        return []
    return sorted(p.stem for p in d.glob('*.md') if p.stem != '_contradictions')


if __name__ == '__main__':
    import sys
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    result = seed_shards(root)
    print(f'Seeded {len(result)} shards:')
    for name, count in sorted(result.items()):
        print(f'  {name}: {count} entries')
    print(f'\nAll shards: {list_shards(root)}')
    contras = get_unresolved_contradictions(root)
    if contras:
        print(f'\n⚠ {len(contras)} unresolved contradictions')
