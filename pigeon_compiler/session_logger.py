"""session_logger.py — Per-file LLM session capture for pigeon files.

Records every mutation of a pigeon file as a JSONL entry in
logs/pigeon_sessions/{name}_seq{NNN}.jsonl.  One line per commit.

Each session entry captures:
  - commit hash + full message (the "prompt" / intent)
  - diff stat (insertions, deletions, files)
  - tokens before → after
  - version before → after
  - timestamp (UTC ISO)
  - renamed from → to (if applicable)

Usage from git_plugin.py:
    from pigeon_compiler.session_logger import log_session
    log_session(root, rel_path, entry, commit_hash, commit_msg, diff_stat)
"""
import json
from datetime import datetime, timezone
from pathlib import Path

SESSIONS_DIR = Path('logs/pigeon_sessions')


def _session_file(root: Path, name: str, seq: int) -> Path:
    d = root / SESSIONS_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d / f'{name}_seq{seq:03d}.jsonl'


def log_session(
    root: Path,
    rel_path: str,
    entry: dict,
    commit_hash: str,
    commit_msg: str,
    diff_stat: str = '',
    old_path: str | None = None,
    tokens_before: int = 0,
) -> None:
    """Append one session record to the file's JSONL log."""
    record = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'hash': commit_hash,
        'msg': commit_msg.strip(),
        'intent': entry.get('intent', ''),
        'ver_before': max(1, entry.get('ver', 1) - 1),
        'ver_after': entry.get('ver', 1),
        'tokens_before': tokens_before,
        'tokens_after': entry.get('tokens', 0),
        'diff': diff_stat,
        'path': rel_path,
    }
    if old_path and old_path != rel_path:
        record['renamed_from'] = old_path

    fp = _session_file(root, entry.get('name', 'unknown'), entry.get('seq', 0))
    with open(fp, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')


def count_sessions(root: Path, name: str, seq: int) -> int:
    """Count how many session records exist for a given file."""
    fp = _session_file(root, name, seq)
    if not fp.exists():
        return 0
    return sum(1 for _ in open(fp, encoding='utf-8') if _.strip())


def read_sessions(root: Path, name: str, seq: int) -> list[dict]:
    """Read all session records for a given file."""
    fp = _session_file(root, name, seq)
    if not fp.exists():
        return []
    sessions = []
    with open(fp, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                sessions.append(json.loads(line))
    return sessions
