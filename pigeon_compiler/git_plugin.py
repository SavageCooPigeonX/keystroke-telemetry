"""git_plugin.py — Post-commit pigeon auto-rename daemon.

Fires after every git commit.  Renames touched pigeon files with
living metadata so `ls` shows what each file does and what last changed.

The filename IS the changelog:
  noise_filter_seq007_v004_d0315__filter_live_noise_lc_fixed_timeout.py
  ├─ filter_live_noise     = what this file DOES   (from docstring)
  └─ fixed_timeout         = what was LAST CHANGED (from commit message)

Pipeline:
  1. Skip [pigeon-auto] commits (prevent infinite loops)
  2. Parse commit message → intent slug (max 3 words)
  3. For each changed pigeon file:
     · Docstring → desc slug (what the file IS)
     · Bump version + update date
     · Build import_map (old_module → new_module)
  4. Rewrite all imports across codebase (BEFORE renaming files)
  5. Rename files on disk
  6. Inject prompt box headers + log sessions
  7. Update pigeon_registry.json
  8. Rebuild all MANIFEST.md files
  9. Auto-commit [pigeon-auto]

Install: .git/hooks/post-commit calls `python -m pigeon_compiler.git_plugin`
"""
import ast
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from pigeon_compiler.rename_engine import (
    extract_desc_slug,
    load_registry,
    save_registry,
    build_pigeon_filename,
    parse_pigeon_stem,
    bump_version,
    rewrite_all_imports,
    build_all_manifests,
    validate_imports,
)
from pigeon_compiler.pigeon_limits import is_excluded
from pigeon_compiler.session_logger import log_session, count_sessions

# ── Token estimation ─────────────────────────────────────
# GPT/Claude average ≈ 1 token per 4 chars.  We count the file
# content to give a rough cost estimate per file per mutation.
TOKEN_RATIO = 4  # chars per token


def _estimate_tokens(text: str) -> int:
    """Estimate LLM token count from raw text (1 tok ≈ 4 chars)."""
    return max(1, len(text) // TOKEN_RATIO)


# ── Prompt box regex ────────────────────────────────────
BOX_RE = re.compile(
    r'^# ── pigeon ─[^\n]*\n(?:# [^\n]*\n)*# ─{10,}─*\n',
    re.MULTILINE,
)
_ROOT_DEBUG = re.compile(r'^_')


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


def _git(*args: str) -> str:
    r = subprocess.run(
        ['git', *args],
        capture_output=True, text=True, encoding='utf-8',
        cwd=str(_root()), timeout=30,
    )
    return r.stdout.strip()


# ── Git helpers ─────────────────────────────────────────

def _commit_msg() -> str:
    return _git('log', '-1', '--format=%B')


def _commit_hash() -> str:
    return _git('log', '-1', '--format=%h')


def _changed_files() -> list[str]:
    try:
        raw = _git('diff', '--name-only', 'HEAD~1', 'HEAD')
        return [f for f in raw.splitlines() if f.strip()]
    except Exception:
        return []


def _file_diff_stat(rel: str) -> str:
    """Get compact diff stat for one file (e.g. '+12 -3')."""
    try:
        raw = _git('diff', '--numstat', 'HEAD~1', 'HEAD', '--', rel)
        if raw.strip():
            parts = raw.strip().split('\t')
            if len(parts) >= 2:
                return f'+{parts[0]} -{parts[1]}'
    except Exception:
        pass
    return ''


# ── Intent parsing ──────────────────────────────────────

def _parse_intent(msg: str) -> str:
    """Commit message → 3-word intent slug.

    'feat: Hush spy mode + hero image' → 'hush_spy_mode'
    'fix: apply directory hero image'  → 'fix_directory_hero'
    """
    line = msg.split('\n')[0].strip()
    m = re.match(
        r'^(?:feat|fix|chore|refactor|docs|test|ci)(?:\([^)]+\))?:\s*', line)
    if m:
        line = line[m.end():]
    slug = re.sub(r'[^a-z0-9]+', '_', line.lower()).strip('_')
    words = [w for w in slug.split('_') if w][:3]
    return '_'.join(words) or 'manual_edit'


# ── Prompt box ──────────────────────────────────────────

def _build_box(entry: dict, h: str, lines: int, tokens: int = 0,
               sessions: int = 0) -> str:
    return (
        f'# ── pigeon ────────────────────────────────────\n'
        f'# SEQ: {entry["seq"]:03d} | VER: v{entry["ver"]:03d} | {lines} lines | ~{tokens:,} tokens\n'
        f'# DESC:   {entry.get("desc") or "(none)"}\n'
        f'# INTENT: {entry.get("intent") or "(none)"}\n'
        f'# LAST:   {datetime.now(timezone.utc).strftime("%Y-%m-%d")} @ {h}\n'
        f'# SESSIONS: {sessions}\n'
        f'# ──────────────────────────────────────────────\n'
    )


def _inject_box(fp: Path, entry: dict, h: str, root: Path | None = None):
    try:
        text = fp.read_text(encoding='utf-8')
    except Exception:
        return
    tokens = _estimate_tokens(text)
    sessions = 0
    if root:
        sessions = count_sessions(root, entry.get('name', ''), entry.get('seq', 0))
    box = _build_box(entry, h, len(text.splitlines()), tokens, sessions)
    if '# ── pigeon ─' in text:
        text = BOX_RE.sub(box, text, count=1)
    else:
        end = _ds_end(text)
        if end >= 0:
            text = text[:end] + '\n' + box + text[end:]
        else:
            text = box + text
    fp.write_text(text, encoding='utf-8')


def _ds_end(text: str) -> int:
    """Character index right after the module docstring."""
    try:
        tree = ast.parse(text)
        if not tree.body:
            return -1
        n = tree.body[0]
        if (isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
                and isinstance(n.value.value, str)):
            return sum(len(l) + 1 for l in text.split('\n')[:n.end_lineno])
    except SyntaxError:
        pass
    return -1


# ── Main pipeline ───────────────────────────────────────

def run():
    root = _root()
    msg = _commit_msg()

    if '[pigeon-auto]' in msg:
        return

    h = _commit_hash()
    intent = _parse_intent(msg)
    changed = _changed_files()
    if not changed:
        return

    registry = load_registry(root)
    renames = []        # (old_rel, new_rel, entry, tokens_before, diff_stat)
    box_only = []       # (abs_path, entry, old_rel, tokens_before, diff_stat)
    import_map = {}     # old_module → new_module

    for rel in changed:
        p = Path(rel)
        if p.suffix != '.py' or is_excluded(p):
            continue
        # Root-level debug scripts — skip
        if '/' not in rel and '\\' not in rel and _ROOT_DEBUG.match(p.name):
            continue
        abs_p = root / rel
        if not abs_p.exists():
            continue

        parsed = parse_pigeon_stem(p.stem)
        if not parsed:
            continue

        desc = extract_desc_slug(abs_p) or parsed['desc']
        try:
            file_text = abs_p.read_text(encoding='utf-8')
        except Exception:
            file_text = ''
        tokens = _estimate_tokens(file_text)
        tokens_before = tokens  # snapshot before mutation
        diff_stat = _file_diff_stat(rel)

        entry = registry.get(rel)
        if entry:
            entry = bump_version(entry, new_desc=desc, new_intent=intent)
            entry['tokens'] = tokens
            entry['history'][-1]['tokens'] = tokens
        else:
            today = datetime.now(timezone.utc).strftime('%m%d')
            entry = {
                'path': rel, 'name': parsed['name'],
                'seq': parsed['seq'], 'ver': parsed['ver'] + 1,
                'date': today, 'desc': desc, 'intent': intent,
                'tokens': tokens,
                'history': [{'ver': parsed['ver'] + 1, 'date': today,
                             'desc': desc, 'intent': intent,
                             'tokens': tokens,
                             'action': 'registered'}],
            }

        new_name = build_pigeon_filename(
            parsed['name'], parsed['seq'], entry['ver'],
            entry['date'], desc, intent,
        )
        folder = str(p.parent).replace('\\', '/')
        new_rel = f'{folder}/{new_name}' if folder != '.' else new_name
        entry['path'] = new_rel

        if rel in registry and rel != new_rel:
            del registry[rel]
        registry[new_rel] = entry

        if p.stem != Path(new_name).stem:
            renames.append((rel, new_rel, entry, tokens_before, diff_stat))
            old_mod = str(Path(rel).with_suffix('')).replace('\\', '.').replace('/', '.')
            new_mod = str(Path(new_rel).with_suffix('')).replace('\\', '.').replace('/', '.')
            import_map[old_mod] = new_mod
        else:
            box_only.append((abs_p, entry, rel, tokens_before, diff_stat))

    if not renames and not box_only:
        return

    print(f'\n🐦 Pigeon Git Plugin: {len(renames)} rename(s), '
          f'{len(box_only)} update(s)')

    # Rewrite imports BEFORE renaming files (safe order — old files still exist)
    if import_map:
        changes = rewrite_all_imports(root, import_map)
        if changes:
            files_hit = len({c['file'] for c in changes})
            print(f'  ↳ {len(changes)} import(s) rewritten in {files_hit} file(s)')

    # Execute renames (after imports are updated)
    for old_rel, new_rel, entry, _, _ in renames:
        old_abs, new_abs = root / old_rel, root / new_rel
        if old_abs.exists():
            new_abs.parent.mkdir(parents=True, exist_ok=True)
            old_abs.rename(new_abs)
            print(f'  📝 {Path(old_rel).name}')
            print(f'     → {Path(new_rel).name}')

    # Log sessions + inject prompt boxes
    for old_rel, new_rel, entry, tb, ds in renames:
        log_session(root, new_rel, entry, h, msg, ds, old_path=old_rel, tokens_before=tb)
        new_abs = root / new_rel
        if new_abs.exists():
            _inject_box(new_abs, entry, h, root)
    for abs_p, entry, old_rel, tb, ds in box_only:
        log_session(root, old_rel, entry, h, msg, ds, tokens_before=tb)
        _inject_box(abs_p, entry, h, root)

    # Save registry
    save_registry(root, registry)

    # Rebuild manifests
    try:
        build_all_manifests(root)
    except Exception as e:
        print(f'  ⚠️  Manifest rebuild: {e}')

    # Compute total token footprint for this commit
    total_tokens = sum(
        e.get('tokens', 0) for _, _, e, _, _ in renames
    ) + sum(
        _estimate_tokens(fp.read_text(encoding='utf-8'))
        for fp, _, _, _, _ in box_only if fp.exists()
    )

    # Validate imports before committing — catch broken state early
    if renames:
        val = validate_imports(root)
        if not val['valid']:
            broken = val['broken']
            print(f'  ⚠️  {len(broken)} broken import(s) detected after rename:')
            for b in broken[:10]:
                print(f"      {b['file']}:{b['line']}  {b['import']}")
            # Attempt a second rewrite pass with broader matching
            extra = rewrite_all_imports(root, import_map)
            if extra:
                print(f'  🔧 Second pass fixed {len(extra)} import(s)')

    # Auto-commit
    _git('add', '-A')
    if _git('status', '--porcelain').strip():
        n = len(renames)
        _git('commit', '-m',
             f'chore(pigeon): auto-rename {n} file(s) [pigeon-auto]\n\n'
             f'Intent: {intent}\n'
             f'Tokens: ~{total_tokens:,}\n'
             f'Triggered by: {msg.splitlines()[0]}')
        print(f'  ✅ Auto-committed [pigeon-auto] (~{total_tokens:,} tokens)\n')
    else:
        print(f'  ℹ️  No changes to auto-commit\n')


if __name__ == '__main__':
    try:
        run()
    except Exception as e:
        # Post-commit — never break the workflow
        print(f'  ⚠️  Pigeon plugin error: {e}')
