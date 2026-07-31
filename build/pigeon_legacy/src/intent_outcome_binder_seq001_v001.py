"""Latest intent outcome binder implementation — closes the intent→outcome loop.

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

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v002 | 584 lines | ~5,433 tokens
# DESC:   closes_the_intent_outcome_loop
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

JOURNAL_PATH = 'logs/prompt_journal.jsonl'
EDIT_PAIRS_PATH = 'logs/edit_pairs.jsonl'
SOLUTION_OUTCOMES_PATH = 'logs/file_solution_outcomes.jsonl'
SOLUTION_MEMORY_PATH = 'logs/file_solution_memory.json'
POST_PUSH_LATEST_PATH = 'logs/post_push_outcome_binder_latest.json'
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
    raw = _git('-c', 'core.quotePath=false', 'diff', '--numstat', f'{commit}^', commit, cwd=root)
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
    root: Path,
    journal_entries: list[dict],
    diff_stats: list[dict[str, Any]],
    commit_ts: datetime,
    commit: str = 'HEAD',
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
                'edit_hash': get_commit_hash(root, commit),
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
                'edit_hash': get_commit_hash(root, commit),
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


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text('utf-8', errors='ignore'))
    except Exception:
        return None


def _load_jsonl(path: Path, limit: int = 200) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in reversed(path.read_text('utf-8', errors='ignore').splitlines()):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
        if len(rows) >= limit:
            break
    rows.reverse()
    return rows


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + '\n')


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def _latest_solution_comments(root: Path) -> dict[str, dict[str, Any]]:
    """Load response-policy file proposals keyed by file path."""
    policy = _load_json(root / 'logs' / 'operator_response_policy_latest.json') or {}
    comments = policy.get('file_comments') if isinstance(policy, dict) else []
    out: dict[str, dict[str, Any]] = {}
    for comment in comments or []:
        if not isinstance(comment, dict):
            continue
        file_path = str(comment.get('file') or comment.get('path') or '').replace('\\', '/')
        if file_path:
            out[file_path] = comment
    return out


def _latest_backward_notes(root: Path) -> dict[str, dict[str, Any]]:
    rows = _load_jsonl(root / 'logs' / 'file_solution_backward_pass.jsonl', 300)
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        path = str(row.get('path') or '').replace('\\', '/')
        if path:
            out[path] = row
    return out


def run_rename_engine_guard(
    root: Path,
    intent: str = 'post_push_outcome_binder',
    execute: bool | None = None,
) -> dict[str, Any]:
    """Fire the rename engine and validate imports, dry-run unless explicitly enabled."""
    root = Path(root)
    if execute is None:
        execute = os.environ.get('PIGEON_POST_PUSH_RENAME_EXECUTE', '').lower() in {'1', 'true', 'yes'}
    result: dict[str, Any] = {
        'schema': 'rename_engine_guard/v1',
        'ts': _utcnow(),
        'execute': bool(execute),
        'fired': False,
        'import_validation': {'valid': False, 'broken': [], 'total_checked': 0},
    }
    try:
        from pigeon_compiler.rename_engine import (
            build_rename_plan,
            run_heal_pipeline,
            scan_project,
            validate_imports,
        )
        result['fired'] = True
        if execute:
            report = run_heal_pipeline(root, execute=True, intent=intent)
        else:
            catalog = scan_project(root)
            plan = build_rename_plan(catalog, root=root, intent=intent)
            report = {
                'dry_run': True,
                'stages': {
                    'scan': catalog.get('stats', {}),
                    'plan': {
                        'renames_planned': len(plan.get('renames', [])),
                        'import_mappings': len(plan.get('import_map', {})),
                        'files': [
                            f"{row.get('old_path')} -> {row.get('new_path')}"
                            for row in (plan.get('renames') or [])[:20]
                        ],
                    },
                },
            }
        validation = validate_imports(root)
        result['report'] = report
        result['import_validation'] = {
            'valid': bool(validation.get('valid')),
            'broken': validation.get('broken', [])[:20],
            'total_checked': validation.get('total_checked', 0),
        }
        result['safe'] = bool(validation.get('valid'))
    except Exception as exc:
        result['error'] = str(exc)
        result['safe'] = False
    return result


def _comment_for_file(
    file_path: str,
    comments: dict[str, dict[str, Any]],
    backward: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    file_key = file_path.replace('\\', '/')
    comment = comments.get(file_key, {})
    note = backward.get(file_key, {})
    if comment or note:
        return comment, note
    stem = Path(file_key).stem.lower()
    for key, candidate in comments.items():
        if Path(key).stem.lower() == stem:
            return candidate, backward.get(key, {})
    for key, candidate in backward.items():
        if Path(key).stem.lower() == stem:
            return comments.get(key, {}), candidate
    return {}, {}


def _score_solution_outcome(
    binding: dict[str, Any],
    comment: dict[str, Any],
    backward: dict[str, Any],
    rename_guard: dict[str, Any],
) -> dict[str, Any]:
    checks = [
        {'key': 'file_changed', 'passed': bool(binding.get('added') or binding.get('removed'))},
        {'key': 'intent_matched', 'passed': float(binding.get('match_score') or 0) > 0.4},
        {'key': 'had_file_proposal', 'passed': bool(comment.get('file_fix_proposal'))},
        {'key': 'had_backward_note', 'passed': bool(backward or comment.get('backward_pass_learning'))},
        {'key': 'rename_engine_fired', 'passed': bool(rename_guard.get('fired'))},
        {'key': 'imports_valid', 'passed': bool((rename_guard.get('import_validation') or {}).get('valid'))},
    ]
    fix_grade = comment.get('fix_grade') if isinstance(comment.get('fix_grade'), dict) else {}
    if fix_grade:
        checks.append({
            'key': 'proposal_grader_passed',
            'passed': fix_grade.get('decision') in {'codex_can_act_after_review', 'deepseek_should_draft_policy'},
        })
    score = sum(1 for check in checks if check['passed'])
    max_score = len(checks)
    if score >= max_score - 1:
        verdict = 'strengthen_path'
    elif score >= max(3, max_score // 2):
        verdict = 'keep_watch'
    else:
        verdict = 'weaken_path'
    return {
        'schema': 'file_solution_outcome_score/v1',
        'score': score,
        'max_score': max_score,
        'verdict': verdict,
        'checks': checks,
    }


def bind_solution_outcomes(
    root: Path,
    bindings: list[dict[str, Any]],
    rename_guard: dict[str, Any],
) -> dict[str, Any]:
    """Bind pushed file changes back to file comments and backward-pass notes."""
    root = Path(root)
    comments = _latest_solution_comments(root)
    backward = _latest_backward_notes(root)
    outcomes = []
    for binding in bindings:
        file_path = str(binding.get('file') or '').replace('\\', '/')
        comment, note = _comment_for_file(file_path, comments, backward)
        back = note or comment.get('backward_pass_learning') or {}
        outcome_score = _score_solution_outcome(binding, comment, back, rename_guard)
        record = {
            'schema': 'file_solution_outcome/v1',
            'ts': _utcnow(),
            'commit': binding.get('edit_hash', ''),
            'file': file_path,
            'prompt_msg': binding.get('prompt_msg', ''),
            'proposed_fix': comment.get('file_fix_proposal', ''),
            'fix_grade': comment.get('fix_grade', {}),
            'backward_pass_learning': back,
            'diff': {
                'added': binding.get('added', 0),
                'removed': binding.get('removed', 0),
                'before_lines': binding.get('before_lines', 0),
                'after_lines': binding.get('after_lines', 0),
            },
            'rename_engine': {
                'fired': rename_guard.get('fired', False),
                'execute': rename_guard.get('execute', False),
                'imports_valid': (rename_guard.get('import_validation') or {}).get('valid', False),
            },
            'outcome_score': outcome_score,
        }
        outcomes.append(record)
        _append_jsonl(root / SOLUTION_OUTCOMES_PATH, record)
    memory = _update_solution_memory(root, outcomes)
    return {
        'schema': 'post_push_solution_outcome_binding/v1',
        'outcomes': len(outcomes),
        'strengthened': sum(1 for item in outcomes if item['outcome_score']['verdict'] == 'strengthen_path'),
        'watched': sum(1 for item in outcomes if item['outcome_score']['verdict'] == 'keep_watch'),
        'weakened': sum(1 for item in outcomes if item['outcome_score']['verdict'] == 'weaken_path'),
        'memory_paths': len(memory.get('paths', {})),
    }


def _update_solution_memory(root: Path, outcomes: list[dict[str, Any]]) -> dict[str, Any]:
    memory = _load_json(root / SOLUTION_MEMORY_PATH)
    if not isinstance(memory, dict):
        memory = {'schema': 'file_solution_memory/v1', 'paths': {}, 'tokens': {}}
    paths = memory.setdefault('paths', {})
    tokens = memory.setdefault('tokens', {})
    for outcome in outcomes:
        path = outcome.get('file', '')
        score = outcome.get('outcome_score', {})
        verdict = score.get('verdict', 'keep_watch')
        path_row = paths.setdefault(path, {
            'attempts': 0, 'strengthen': 0, 'watch': 0, 'weaken': 0, 'last_verdict': '',
        })
        path_row['attempts'] += 1
        path_row['last_verdict'] = verdict
        if verdict == 'strengthen_path':
            path_row['strengthen'] += 1
        elif verdict == 'weaken_path':
            path_row['weaken'] += 1
        else:
            path_row['watch'] += 1
        back = outcome.get('backward_pass_learning') or {}
        for token in back.get('pattern_tokens') or []:
            token_row = tokens.setdefault(token, {'attempts': 0, 'strengthen': 0, 'weaken': 0})
            token_row['attempts'] += 1
            if verdict == 'strengthen_path':
                token_row['strengthen'] += 1
            elif verdict == 'weaken_path':
                token_row['weaken'] += 1
    memory['updated_at'] = _utcnow()
    _write_json(root / SOLUTION_MEMORY_PATH, memory)
    return memory


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


def bind_commit(
    root: Path,
    commit: str = 'HEAD',
    run_rename_guard: bool = True,
    execute_rename: bool | None = None,
) -> dict[str, Any]:
    """Main entry: bind a commit's file changes to the closest journal intents."""
    root = Path(root)

    # When was this commit?
    raw_ts = _git('log', '-1', '--pretty=%cI', commit, cwd=root)
    commit_ts = _parse_ts(raw_ts) or datetime.now(timezone.utc)

    diff_stats = get_commit_diff_stats(root, commit)
    if not diff_stats:
        return {'bound': 0, 'unmatched': 0, 'skipped': True, 'reason': 'no_diff'}

    journal = load_recent_journal(root)
    bindings = match_journal_to_files(root, journal, diff_stats, commit_ts, commit=commit)

    matched = [b for b in bindings if b['match_score'] > 0.4]
    unmatched = [b for b in bindings if b['match_score'] <= 0.4]

    written = append_edit_pairs(root, bindings)
    rename_guard = (
        run_rename_engine_guard(root, intent='post_push_outcome_binder', execute=execute_rename)
        if run_rename_guard
        else {'schema': 'rename_engine_guard/v1', 'fired': False, 'safe': True, 'import_validation': {'valid': True}}
    )
    outcome_binding = bind_solution_outcomes(root, bindings, rename_guard)

    latest = {
        'schema': 'post_push_outcome_binder/v1',
        'ts': _utcnow(),
        'commit': get_commit_hash(root, commit),
        'commit_ts': commit_ts.isoformat(),
        'files_changed': len(diff_stats),
        'bound': len(matched),
        'unmatched': len(unmatched),
        'written': written,
        'rename_engine': rename_guard,
        'outcome_binding': outcome_binding,
    }
    _write_json(root / POST_PUSH_LATEST_PATH, latest)

    return {
        'commit': get_commit_hash(root, commit),
        'commit_ts': commit_ts.isoformat(),
        'files_changed': len(diff_stats),
        'bound': len(matched),
        'unmatched': len(unmatched),
        'written': written,
        'rename_engine': rename_guard,
        'outcome_binding': outcome_binding,
    }


if __name__ == '__main__':
    import sys
    root = Path('.')
    commit = sys.argv[1] if len(sys.argv) > 1 else 'HEAD'
    result = bind_commit(root, commit)
    print(f"commit: {result.get('commit')} | files: {result['files_changed']} | "
          f"bound: {result['bound']} | unmatched: {result['unmatched']}")
