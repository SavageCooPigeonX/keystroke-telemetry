"""git_plugin_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from .git_plugin_seq001_v001 import _git
from .git_plugin_seq001_v001 import _root
import re
import subprocess

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


def _intent_code_numeric(intent: str) -> str:
    """Map intent slug to numeric encoding for prompt mapping."""
    if not intent:
        return '00'
    # Simple hash-based numeric encoding (00-99)
    hash_val = sum(ord(ch) for ch in intent)
    return f'{hash_val % 100:02d}'
