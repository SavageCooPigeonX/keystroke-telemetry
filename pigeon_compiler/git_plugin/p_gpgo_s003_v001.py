"""git_plugin_git_ops_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 35 lines | ~255 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re
import subprocess

def _commit_msg() -> str:
    return _git('log', '-1', '--format=%B')


def _commit_hash() -> str:
    return _git('log', '-1', '--format=%h')


def _changed_files() -> list[str]:
    try:
        raw = subprocess.run(
            ['git', '-c', 'core.quotepath=false', 'diff', '--name-only', 'HEAD~1', 'HEAD'],
            capture_output=True, text=True, encoding='utf-8',
            cwd=str(_root()), timeout=30,
        ).stdout.strip()
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
