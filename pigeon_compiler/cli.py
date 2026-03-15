"""pigeon — CLI for the Pigeon Code self-documenting codebase engine.

Usage:
    pigeon init          Install git hooks into the current repo
    pigeon status        Show codebase health (files, tokens, stale intents)
    pigeon heal          One-shot rename of all pigeon files (rebuild manifests)
    pigeon sessions      Show recent session logs across all files
    pigeon uninstall     Remove pigeon git hooks

The filename IS the changelog:
    noise_filter_seq007_v004_d0316__filter_live_noise_lc_fixed_timeout.py
    ├─ filter_live_noise     = what the file DOES  (from docstring)
    └─ fixed_timeout         = what was LAST DONE  (from commit message)
"""
import argparse
import json
import os
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path


def _root() -> Path:
    """Walk up from cwd to find .git directory."""
    p = Path.cwd().resolve()
    while p != p.parent:
        if (p / '.git').is_dir():
            return p
        p = p.parent
    print('ERROR: not inside a git repository.')
    sys.exit(1)


# ── pigeon init ──────────────────────────────────────────

POST_COMMIT_HOOK = '''#!/bin/sh
# Pigeon Code — post-commit auto-rename daemon.
# Renames touched pigeon files with living desc + intent from commit message.
# The filename IS the changelog — ls shows what was last pushed/changed.

MSG=$(git log -1 --format=%B)
case "$MSG" in
  *\\[pigeon-auto\\]*) exit 0 ;;
esac

if [ -f ".venv/Scripts/python.exe" ]; then
    PYTHON=".venv/Scripts/python.exe"
elif [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
else
    PYTHON="python"
fi

"$PYTHON" -m pigeon_compiler.git_plugin || true
'''

PRE_COMMIT_HOOK = '''#!/bin/sh
# Pigeon Code — advisory pre-commit audit.
# Reports compliance but never blocks commits.

if [ -f ".venv/Scripts/python.exe" ]; then
    PYTHON=".venv/Scripts/python.exe"
elif [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON="python3"
else
    PYTHON="python"
fi

"$PYTHON" -m pigeon_compiler.pre_commit_audit || true
exit 0
'''


def _make_executable(path: Path):
    """Add executable permission (needed on Unix)."""
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


def cmd_init(args):
    root = _root()
    hooks_dir = root / '.git' / 'hooks'
    hooks_dir.mkdir(parents=True, exist_ok=True)

    # Post-commit hook
    post = hooks_dir / 'post-commit'
    if post.exists() and '[pigeon-auto]' not in post.read_text(encoding='utf-8'):
        print(f'  ⚠️  {post} already exists (not pigeon). Backing up...')
        post.rename(post.with_suffix('.bak'))
    post.write_text(POST_COMMIT_HOOK, encoding='utf-8')
    _make_executable(post)
    print(f'  ✅ Installed post-commit hook')

    # Pre-commit hook
    pre = hooks_dir / 'pre-commit'
    if pre.exists() and 'pigeon_compiler' not in pre.read_text(encoding='utf-8'):
        print(f'  ⚠️  {pre} already exists (not pigeon). Backing up...')
        pre.rename(pre.with_suffix('.bak'))
    pre.write_text(PRE_COMMIT_HOOK, encoding='utf-8')
    _make_executable(pre)
    print(f'  ✅ Installed pre-commit hook')

    # Create registry if missing
    reg_path = root / 'pigeon_registry.json'
    if not reg_path.exists():
        data = {'generated': datetime.now(timezone.utc).isoformat(),
                'total': 0, 'files': []}
        reg_path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
        print(f'  ✅ Created pigeon_registry.json')

    # Create session log dir
    sessions_dir = root / 'logs' / 'pigeon_sessions'
    sessions_dir.mkdir(parents=True, exist_ok=True)
    print(f'  ✅ Created logs/pigeon_sessions/')

    print(f'\n🐦 Pigeon Code initialized in {root}')
    print(f'   Every commit now auto-renames pigeon files with intent from commit message.')
    print(f'   Run `pigeon status` to see codebase health.')


# ── pigeon status ────────────────────────────────────────

def cmd_status(args):
    root = _root()
    reg_path = root / 'pigeon_registry.json'
    if not reg_path.exists():
        print('No pigeon_registry.json found. Run `pigeon init` first.')
        return

    data = json.loads(reg_path.read_text(encoding='utf-8'))
    files = data.get('files', [])
    pigeon = [f for f in files if f.get('seq', 0) > 0]
    stale = [f for f in pigeon if f.get('intent') == 'desc_upgrade']
    has_tokens = [f for f in pigeon if f.get('tokens')]
    total_tokens = sum(f.get('tokens', 0) for f in pigeon)
    real_intent = [f for f in pigeon if f.get('intent') and f['intent'] != 'desc_upgrade']

    # Check hooks
    hooks_dir = root / '.git' / 'hooks'
    has_post = (hooks_dir / 'post-commit').exists()
    has_pre = (hooks_dir / 'pre-commit').exists()

    # Session count
    sessions_dir = root / 'logs' / 'pigeon_sessions'
    session_files = list(sessions_dir.glob('*.jsonl')) if sessions_dir.exists() else []
    total_sessions = 0
    for sf in session_files:
        total_sessions += sum(1 for line in open(sf, encoding='utf-8') if line.strip())

    print(f'\n🐦 Pigeon Code Status — {root.name}')
    print(f'   ──────────────────────────────────')
    print(f'   Files:        {len(files)} total, {len(pigeon)} pigeon-coded')
    print(f'   Tokens:       ~{total_tokens:,} across codebase')
    print(f'   With tokens:  {len(has_tokens)}/{len(pigeon)}')
    print(f'   Real intent:  {len(real_intent)} (renamed by commits)')
    print(f'   Stale:        {len(stale)} still _lc_desc_upgrade')
    print(f'   Sessions:     {total_sessions} logged across {len(session_files)} files')
    print(f'   Hooks:        post-commit={"✅" if has_post else "❌"}  pre-commit={"✅" if has_pre else "❌"}')
    print()

    if stale:
        pct = len(real_intent) / len(pigeon) * 100 if pigeon else 0
        print(f'   {pct:.0f}% of pigeon files have real intent.')
        print(f'   The other {len(stale)} will self-heal as you commit changes to them.')


# ── pigeon heal ──────────────────────────────────────────

def cmd_heal(args):
    root = _root()
    print(f'\n🐦 Running pigeon heal on {root.name}...')

    # Import here so CLI loads fast
    from pigeon_compiler.rename_engine import (
        load_registry, save_registry, build_all_manifests,
    )
    from pigeon_compiler.git_plugin import _estimate_tokens, _inject_box

    registry = load_registry(root)
    updated = 0

    for rel, entry in sorted(registry.items()):
        if entry.get('seq', 0) == 0:
            continue
        fp = root / rel
        if not fp.exists() or fp.suffix != '.py':
            continue

        try:
            text = fp.read_text(encoding='utf-8')
        except Exception:
            continue

        tokens = _estimate_tokens(text)
        changed = False

        if not entry.get('tokens'):
            entry['tokens'] = tokens
            changed = True

        if '# ── pigeon ─' not in text:
            _inject_box(fp, entry, 'heal', root)
            changed = True

        if changed:
            updated += 1

    save_registry(root, registry)

    try:
        build_all_manifests(root)
        print(f'   ✅ Manifests rebuilt')
    except Exception as e:
        print(f'   ⚠️  Manifest rebuild: {e}')

    print(f'   ✅ Updated {updated} files (prompt boxes + token counts)')
    print(f'   📦 Registry saved ({len(registry)} entries)')


# ── pigeon sessions ──────────────────────────────────────

def cmd_sessions(args):
    root = _root()
    sessions_dir = root / 'logs' / 'pigeon_sessions'
    if not sessions_dir.exists():
        print('No session logs found. Run `pigeon init` and start committing.')
        return

    files = sorted(sessions_dir.glob('*.jsonl'))
    if not files:
        print('No session logs yet. Commit changes to pigeon files to generate logs.')
        return

    print(f'\n🐦 Session Logs — {root.name}')
    print(f'   ──────────────────────────────────')

    all_sessions = []
    for f in files:
        for line in open(f, encoding='utf-8'):
            line = line.strip()
            if line:
                rec = json.loads(line)
                rec['_file'] = f.stem
                all_sessions.append(rec)

    # Sort by timestamp, show most recent
    all_sessions.sort(key=lambda r: r.get('ts', ''), reverse=True)
    limit = args.limit if hasattr(args, 'limit') else 20

    for s in all_sessions[:limit]:
        ts = s.get('ts', '')[:19].replace('T', ' ')
        intent = s.get('intent', '?')
        ver = f"v{s.get('ver_before', '?')}→v{s.get('ver_after', '?')}"
        diff = s.get('diff', '')
        name = s.get('_file', '?')
        msg = s.get('msg', '')[:60]
        print(f'   {ts}  {name}  {ver}  {diff}  [{intent}]')
        print(f'     └─ {msg}')

    if len(all_sessions) > limit:
        print(f'\n   ... and {len(all_sessions) - limit} more. Use --limit N to see more.')


# ── pigeon uninstall ─────────────────────────────────────

def cmd_uninstall(args):
    root = _root()
    hooks_dir = root / '.git' / 'hooks'

    for name in ('post-commit', 'pre-commit'):
        hook = hooks_dir / name
        if hook.exists():
            text = hook.read_text(encoding='utf-8')
            if 'pigeon' in text.lower():
                bak = hook.with_suffix('.bak')
                if bak.exists():
                    bak.rename(hook)
                    print(f'  ✅ Restored {name} from backup')
                else:
                    hook.unlink()
                    print(f'  ✅ Removed {name} hook')
            else:
                print(f'  ⏭️  {name} is not a pigeon hook, skipping')

    print(f'\n🐦 Pigeon hooks removed. Registry and session logs preserved.')


# ── main ─────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog='pigeon',
        description='Pigeon Code — self-documenting codebase engine. '
                    'Filenames mutate on every commit to carry intent.',
    )
    sub = parser.add_subparsers(dest='command')

    sub.add_parser('init', help='Install pigeon git hooks into current repo')
    sub.add_parser('status', help='Show codebase health metrics')
    sub.add_parser('heal', help='Bulk inject prompt boxes + rebuild manifests')

    sp_sessions = sub.add_parser('sessions', help='Show recent session logs')
    sp_sessions.add_argument('--limit', type=int, default=20,
                             help='Max sessions to show (default: 20)')

    sub.add_parser('uninstall', help='Remove pigeon git hooks')

    args = parser.parse_args()

    commands = {
        'init': cmd_init,
        'status': cmd_status,
        'heal': cmd_heal,
        'sessions': cmd_sessions,
        'uninstall': cmd_uninstall,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
