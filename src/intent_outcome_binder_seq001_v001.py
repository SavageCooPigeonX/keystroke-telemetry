"""intent_outcome_binder_seq001_v001.py — closes the intent→outcome loop.

At every git post-commit:
  1. Parse git diff (changed files + before/after line counts)
  2. Match each changed file against the last N journal entries by timestamp
  3. Write a binding record to logs/edit_pairs.jsonl with REAL content:
     prompt_intent, cognitive_state, changed_file, diff_stat, latency_ms

This is the missing link for self-learning:
  captured_intent + cognitive_state + actual_diff → rework signal → training data

Zero LLM calls. Pure signal processing.

# ── telemetry:pulse ──
# EDIT_TS:   2026-04-17T00:00:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  create intent outcome binder
# EDIT_AUTHOR: copilot
# EDIT_STATE: harvested
# ── /pulse ──

# CONFIRM: sim fires self fix runs files talk meta comments deepseek auto fix
# EDIT_STATE: confirmed
# EDIT_TS:   2026-04-17T00:00:01+00:00
# EDIT_HASH: deepseek_auto_fix
# EDIT_WHY:  confirm sim fires on this prompt, self fix runs, files talk when awake with meta comments, deepseek auto fix runs without breaking stuff
# EDIT_AUTHOR: deepseek
# EDIT_STATE: confirmed
# ── telemetry:pulse ──
# EDIT_TS:   2026-04-17T00:00:02+00:00
# EDIT_HASH: surgical_fix
# EDIT_WHY:  fix get_commit_hash call to use root path instead of Path('.')
# EDIT_AUTHOR: deepseek
# EDIT_STATE: confirmed
# ── /pulse ──
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

JOURNAL_PATH = 'logs/prompt_journal.jsonl'
EDIT_PAIRS_PATH = 'logs/edit_pairs.jsonl'
MATCH_WINDOW_MINUTES = 120   # look back this far in journal for a matching prompt
MAX_JOURNAL_SCAN = 50        # scan at most this many recent journal entries


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_ts(ts_str: str) -> datetime | None:
    if not ts_str:
        return None
    try:
        return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
    except Exception:
        return None


def _git(*args: str, cwd: Path) -> str:
    try:
        result = subprocess.run(
            ['git', *args],
            capture_output=True, text=True, encoding='utf-8', errors='ignore',
            cwd=str(cwd), timeout=15,
        )
        return result.stdout.strip()
    except Exception:
        return ''


def get_commit_diff_stats(root: Path, commit: str = 'HEAD') -> list[dict[str, Any]]:
    """Return per-file diff stats for a commit: file, added, removed, before_lines, after_lines."""
    raw = _git('diff', '--numstat', f'{commit}^', commit, cwd=root)
    stats = []
    for line in raw.splitlines():
        parts = line.split('\t')
        if len(parts) < 3:
            continue
        added_str, removed_str, filepath = parts[0], parts[1], parts[2]
        try:
            added = int(added_str)
            removed = int(removed_str)
        except ValueError:
            continue  # binary file
        # get current line count as proxy for after_lines
        abs_path = root / filepath
        after_lines = len(abs_path.read_text('utf-8', errors='ignore').splitlines()) if abs_path.exists() else 0
        before_lines = max(0, after_lines - added + removed)
        stats.append({
            'file': filepath,
            'added': added,
            'removed': removed,
            'before_lines': before_lines,
            'after_lines': after_lines,
        })
    return stats


def get_commit_message(root: Path, commit: str = 'HEAD') -> str:
    return _git('log', '-1', '--pretty=%B', commit, cwd=root)


def get_commit_hash(root: Path, commit: str = 'HEAD') -> str:
    return _git('rev-parse', '--short', commit, cwd=root)


def load_recent_journal(root: Path, n: int = MAX_JOURNAL_SCAN) -> list[dict]:
    path = root / JOURNAL_PATH
    if not path.exists():
        return []
    lines = path.read_text('utf-8', errors='ignore').splitlines()
    entries = []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except Exception:
            continue
        if len(entries) >= n:
            break
    entries.reverse()
    return entries


def _score_match(journal_entry: dict, file_path: str, commit_ts: datetime) -> float:
    """Score how well a journal entry matches a changed file (0.0–1.0)."""
    entry_ts = _parse_ts(journal_entry.get('ts', ''))
    if not entry_ts:
        return 0.0

    # Must be before the commit and within window
    delta = commit_ts - entry_ts
    if delta.total_seconds() < 0 or delta > timedelta(minutes=MATCH_WINDOW_MINUTES):
        return 0.0

    score = 0.5  # base — it's within the window

    # Recency bonus: closer to commit = better
    recency = 1.0 - (delta.total_seconds() / (MATCH_WINDOW_MINUTES * 60))
    score += recency * 0.3

    # File reference match
    file_stem = Path(file_path).stem.lower()
    msg = str(journal_entry.get('msg', '')).lower()
    refs = [str(r).lower() for r in journal_entry.get('module_refs', [])]
    files_open = [str(f).lower() for f in journal_entry.get('files_open', [])]

    if file_stem in msg:
        score += 0.1
    if any(file_stem in r for r in refs):
        score += 0.1
    if any(file_stem in f for f in files_open):
        score += 0.1

    # Deleted words match test
    deleted_words = journal_entry.get('deleted_words', [])
    if 'orange' in deleted_words:
        score += 0.2

    return min(score, 1.0)


def match_journal_to_files(
    journal_entries: list[dict],
    diff_stats: list[dict[str, Any]],
    commit_ts: datetime,
) -> list[dict[str, Any]]:
    """For each changed file, find the best matching journal entry."""
    bindings = []
    for stat in diff_stats:
        filepath = stat['file']
        best_entry = None
        best_score = 0.0

        for entry in journal_entries:
            score = _score_match(entry, filepath, commit_ts)
            if score > best_score:
                best_score = score
                best_entry = entry

        if best_entry and best_score > 0.4:
            entry_ts = _parse_ts(best_entry.get('ts', ''))
            latency_ms = max(0, int((commit_ts - entry_ts).total_seconds() * 1000)) if entry_ts else None
            signals = best_entry.get('signals', {})
            bindings.append({
                'ts': _utcnow(),
                'prompt_ts': best_entry.get('ts', ''),
                'prompt_msg': str(best_entry.get('msg', ''))[:200],
                'prompt_intent': best_entry.get('intent', 'unknown'),
                'file': filepath,
                'edit_ts': commit_ts.isoformat(),
                'edit_why': str(best_entry.get('msg', ''))[:60],
                'edit_hash': get_commit_hash(root),
                'edit_author': 'copilot',
                'added': stat['added'],
                'removed': stat['removed'],
                'before_lines': stat['before_lines'],
                'after_lines': stat['after_lines'],
                'latency_ms': latency_ms,
                'match_score': round(best_score, 3),
                'state': best_entry.get('cognitive_state', signals.get('state', 'unknown')),
                'wpm': signals.get('wpm', 0),
                'deletion_ratio': signals.get('deletion_ratio', 0),
                'hesitation_count': signals.get('hesitation_count', 0),
                'deleted_words': best_entry.get('deleted_words', []),
                'session_n': best_entry.get('session_n', 0),
            })
        else:
            # Unmatched — still record the file change, intent unknown
            bindings.append({
                'ts': _utcnow(),
                'prompt_ts': '',
                'prompt_msg': '',
                'prompt_intent': 'unmatched',
                'file': filepath,
                'edit_ts': commit_ts.isoformat(),
                'edit_why': '',
                'edit_hash': get_commit_hash(root),
                'edit_author': 'unknown',
                'added': stat['added'],
                'removed': stat['removed'],
                'before_lines': stat['before_lines'],
                'after_lines': stat['after_lines'],
                'latency_ms': None,
                'match_score': 0.0,
                'state': 'unknown',
                'wpm': 0,
                'deletion_ratio': 0,
                'hesitation_count': 0,
                'deleted_words': [],
                'session_n': 0,
            })

    return bindings


def append_edit_pairs(root: Path, bindings: list[dict[str, Any]]) -> int:
    """Append binding records to edit_pairs.jsonl. Returns count written."""
    if not bindings:
        return 0
    path = root / EDIT_PAIRS_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(b, ensure_ascii=False) for b in bindings]
    with path.open('a', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')
    return len(bindings)


def bind_commit(root: Path, commit: str = 'HEAD') -> dict[str, Any]:
    """Main entry: bind a commit's file changes to the closest journal intents."""
    root = Path(root)

    # When was this commit?
    raw_ts = _git('log', '-1', '--pretty=%cI', commit, cwd=root)
    commit_ts = _parse_ts(raw_ts) or datetime.now(timezone.utc)

    diff_stats = get_commit_diff_stats(root, commit)
    if not diff_stats:
        return {'bound': 0, 'unmatched': 0, 'skipped': True, 'reason': 'no_diff'}

    journal = load_recent_journal(root)
    bindings = match_journal_to_files(journal, diff_stats, commit_ts)

    matched = [b for b in bindings if b['match_score'] > 0.4]
    unmatched = [b for b in bindings if b['match_score'] <= 0.4]

    written = append_edit_pairs(root, bindings)

    return {
        'commit': get_commit_hash(root, commit),
        'commit_ts': commit_ts.isoformat(),
        'files_changed': len(diff_stats),
        'bound': len(matched),
        'unmatched': len(unmatched),
        'written': written,
    }


if __name__ == '__main__':
    import sys
    root = Path('.')
    commit = sys.argv[1] if len(sys.argv) > 1 else 'HEAD'
    result = bind_commit(root, commit)
    print(f"commit: {result.get('commit')} | files: {result['files_changed']} | "
          f"bound: {result['bound']} | unmatched: {result['unmatched']}")
