"""deepseek_daemon_seq001_v001 — Always-on parallel DeepSeek compiler/fixer.

DeepSeek runs continuously alongside the operator and Copilot.
It acts as the compress/compile layer — maintaining pigeon code compliance,
fixing known bugs, draining the intent backlog, and actually coding.

Work sources (priority order):
  1. intent_jobs.jsonl (status=simulated, top_files with grade > 0.0)
  2. pigeon_registry.json  — βoc (over_hard_cap), hi (hardcoded_import), de (dead_export)
  3. logs/post_patch_grades.jsonl — rejected patches → retry with re-framed intent
  4. escalation_engine level 4 (ACT) candidates

Cadence: one DeepSeek call per CYCLE_S seconds (default 45s). Rate-safe.

Launch: py src/deepseek_daemon_seq001_v001.py
        py src/deepseek_daemon_seq001_v001.py --dry-run   # no writes, log only
        py src/deepseek_daemon_seq001_v001.py --once      # single cycle then exit
"""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001
# DESC:   always_on_deepseek_compiler_daemon
# INTENT: feat_self_heal
# LAST:   2026-04-22
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   2026-04-22T06:00:00+00:00
# EDIT_HASH: auto
# EDIT_WHY:  initial — always-on deepseek parallel fixer
# EDIT_AUTHOR: copilot
# EDIT_STATE: active
# ── /pulse ──

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).parent.parent
LOGS = ROOT / 'logs'
DAEMON_LOG = LOGS / 'deepseek_daemon.jsonl'
INTENT_JOBS = LOGS / 'intent_jobs.jsonl'
OVERWRITE_LOG = LOGS / 'file_overwrites.jsonl'
POST_GRADE_LOG = LOGS / 'post_patch_grades.jsonl'

CYCLE_S = 45            # minimum seconds between DeepSeek calls
MAX_GRADE_RETRY = 2     # max retries for a rejected patch
INTENT_MIN_GRADE = 0.1  # minimum sim grade to attempt a fix

_DEEPSEEK_URL = 'https://api.deepseek.com/v1/chat/completions'
_DEEPSEEK_MODEL = 'deepseek-chat'


# ── helpers ────────────────────────────────────────────────────────────────────

def _load_api_key() -> str | None:
    key = os.environ.get('DEEPSEEK_API_KEY', '')
    if key:
        return key
    env = ROOT / '.env'
    if env.exists():
        for line in env.read_text(encoding='utf-8').splitlines():
            if line.startswith('DEEPSEEK_API_KEY='):
                return line.split('=', 1)[1].strip().strip('"').strip("'")
    return None


def _log(entry: dict):
    DAEMON_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry['ts'] = datetime.now(timezone.utc).isoformat()
    with open(DAEMON_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    print(f'[daemon] {entry.get("action","?")} {entry.get("stem","")}: {entry.get("result","")[:80]}')


def _load_glob_module(folder: str, pattern: str):
    matches = sorted((ROOT / folder).glob(f'{pattern}.py'))
    if not matches:
        return None
    path = matches[-1]
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if not spec or not spec.loader:
        return None
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        return mod
    except Exception as e:
        print(f'[daemon] import failed {path.name}: {e}')
        return None


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text('utf-8', errors='ignore').strip().splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def _call_deepseek(system: str, user: str, api_key: str, max_tokens: int = 2000) -> str | None:
    import urllib.request
    body = json.dumps({
        'model': _DEEPSEEK_MODEL,
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user},
        ],
        'max_tokens': max_tokens,
        'temperature': 0.15,
    }).encode('utf-8')
    req = urllib.request.Request(
        _DEEPSEEK_URL, data=body,
        headers={'Content-Type': 'application/json',
                 'Authorization': f'Bearer {api_key}'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return data['choices'][0]['message']['content']
    except Exception as e:
        print(f'[daemon] deepseek call failed: {e}')
        return None


def _is_file_busy(stem: str) -> bool:
    """Check if a file's pulse header says it's actively being edited."""
    matches = list((ROOT / 'src').glob(f'{stem}*.py'))
    if not matches:
        return False
    try:
        source = matches[-1].read_text('utf-8', errors='ignore')
        for line in source.splitlines()[:25]:
            if 'EDIT_STATE' in line and 'active' in line:
                return True
    except Exception:
        pass
    return False


# ── work sources ───────────────────────────────────────────────────────────────

def _intent_work(already_attempted: set[str]) -> list[dict]:
    """Pull simulated intent jobs that have file grades and haven't been tried."""
    jobs = _read_jsonl(INTENT_JOBS)
    work = []
    for job in reversed(jobs):   # newest first
        if job.get('status') != 'simulated':
            continue
        intent = job.get('intent_text', '')
        intent_id = job.get('intent_id', '')
        top_files = job.get('top_files', [])
        grades = job.get('grades', {})
        task_chain = job.get('task_chain', [])
        if not intent or not top_files:
            continue
        # Prefer task_chain entries (filled templates) over raw intent
        if task_chain:
            for task in task_chain:
                stem = task.get('stem', '')
                if not stem:
                    continue
                key = f'intent:{stem}:{intent[:40]}'
                if key in already_attempted:
                    continue
                if task.get('grade', 0.0) < INTENT_MIN_GRADE:
                    continue
                if _is_file_busy(stem):
                    continue
                work.append({
                    'type': 'intent',
                    'stem': stem,
                    'intent': task.get('action', intent),   # filled template action, not raw intent
                    'intent_full': intent,
                    'intent_id': intent_id,
                    'grade': task.get('grade', 0.0),
                    'fix_type': task.get('fix_type', 'fix'),
                    'confidence': task.get('confidence', 0.0),
                    'key': key,
                })
        else:
            # Legacy: no task_chain — fall back to raw grades
            for stem in top_files:
                key = f'intent:{stem}:{intent[:40]}'
                if key in already_attempted:
                    continue
                grade = grades.get(stem, 0.0)
                if grade < INTENT_MIN_GRADE:
                    continue
                if _is_file_busy(stem):
                    continue
                work.append({
                    'type': 'intent',
                    'stem': stem,
                    'intent': intent,
                    'intent_full': intent,
                    'intent_id': intent_id,
                    'grade': grade,
                    'key': key,
                })
    return work[:3]  # max 3 pending at once


def _pigeon_compliance_work(already_attempted: set[str]) -> list[dict]:
    """Pull pigeon registry bugs — hi, oc, de violations."""
    reg_path = ROOT / 'pigeon_registry.json'
    if not reg_path.exists():
        return []
    try:
        reg = json.loads(reg_path.read_text('utf-8'))
    except Exception:
        return []

    files = reg if isinstance(reg, list) else reg.get('files', [])
    work = []
    for entry in files:
        stem = entry.get('name', '') or entry.get('stem', '')
        if not stem:
            continue
        bugs = entry.get('bugs', [])
        if not bugs:
            continue
        for bug in bugs:
            key = f'pigeon:{stem}:{bug}'
            if key in already_attempted:
                continue
            if _is_file_busy(stem):
                continue
            # map pigeon bug codes to actionable descriptions
            if bug in ('hi', 'hardcoded_import'):
                work.append({'type': 'pigeon_compliance', 'stem': stem, 'bug': bug,
                             'intent': f'fix hardcoded import in {stem} — replace with _load_glob_module dynamic pattern',
                             'key': key, 'priority': 2})
            elif bug in ('oc', 'over_hard_cap'):
                tokens = entry.get('tokens', 0)
                work.append({'type': 'pigeon_compliance', 'stem': stem, 'bug': bug,
                             'intent': f'file {stem} is {tokens} tokens over hard cap 2000 — identify natural split boundary and propose split',
                             'key': key, 'priority': 1})
            elif bug in ('de', 'dead_export'):
                work.append({'type': 'pigeon_compliance', 'stem': stem, 'bug': bug,
                             'intent': f'remove dead export(s) from {stem} — clean unused functions nobody imports',
                             'key': key, 'priority': 3})
    # sort by priority asc (1 = highest)
    work.sort(key=lambda x: x.get('priority', 9))
    return work[:2]


def _rejected_patch_work(already_attempted: set[str]) -> list[dict]:
    """Find patches that were rejected by the post-patch grader — retry with new approach."""
    grades = _read_jsonl(POST_GRADE_LOG)
    work = []
    for g in reversed(grades):
        if g.get('verdict') != 'reject':
            continue
        stem = g.get('stem', '')
        intent = g.get('intent_text', '')
        issues = g.get('issues', '')
        key = f'retry:{stem}:{intent[:40]}'
        if key in already_attempted or not stem or not intent:
            continue
        if _is_file_busy(stem):
            continue
        work.append({
            'type': 'retry_rejected',
            'stem': stem,
            'intent': f'{intent} [prev rejected: {issues[:80]}]',
            'key': key,
        })
    return work[:1]


# ── DeepSeek actions ───────────────────────────────────────────────────────────

_COMPILE_SYSTEM = """You are the DeepSeek compiler for a Python codebase that uses the Pigeon naming system.

Your job: surgically fix the stated bug or implement the stated intent in the target file.
You have full awareness of pigeon code compliance rules:
- Files must not hardcode sibling imports — use glob-based dynamic load: `_load_glob_module(root, 'src', 'stem_pattern*')`
- Files over 2000 tokens get split — identify the natural boundary if over cap
- Dead exports get removed — clean unused public functions
- Every file must have the pigeon pulse header: EDIT_TS, EDIT_HASH, EDIT_WHY, EDIT_AUTHOR, EDIT_STATE

Output ONLY surgical search-replace blocks:

<<<SEARCH
<exact lines from file — include 2-3 lines context before/after target>
===
<replacement lines>
>>>REPLACE

If nothing needs changing: NO_CHANGES
No explanation. No markdown. Only blocks."""

_ANALYSIS_SYSTEM = """You are a code compliance auditor for the Pigeon system.
Given a file's source and a bug type, explain:
1. Where exactly the bug is (function name, line pattern)
2. The minimal fix
3. Whether the fix is safe (yes/no/maybe) and why

Be concise — 3-5 sentences max. No code output."""


def _do_fix(work: dict, api_key: str, dry_run: bool) -> dict:
    """Run one DeepSeek fix cycle for a work item. Returns result dict."""
    stem = work['stem']
    intent = work['intent']
    work_type = work['type']

    # find the file
    src_matches = sorted((ROOT / 'src').glob(f'{stem}*.py'))
    if not src_matches:
        # try other common locations
        for folder in ['pigeon_compiler', 'pigeon_compiler/git_plugin', 'client']:
            src_matches = sorted((ROOT / folder).glob(f'{stem}*.py'))
            if src_matches:
                break
    if not src_matches:
        return {'success': False, 'reason': f'file not found for stem {stem}'}

    fpath = src_matches[-1]
    try:
        source = fpath.read_text('utf-8', errors='ignore')
    except Exception as e:
        return {'success': False, 'reason': f'read failed: {e}'}

    # truncate source to stay under DeepSeek context — send first 400 lines max
    lines = source.splitlines()
    if len(lines) > 400:
        source_trunc = '\n'.join(lines[:400]) + f'\n\n# ... {len(lines)-400} more lines truncated'
    else:
        source_trunc = source

    # ── Split lineage: tell DeepSeek if this file was born from a split ──
    _lineage_ctx = ''
    try:
        import json as _json
        _split_log = ROOT / 'logs' / 'split_events.jsonl'
        if _split_log.exists():
            _lin_map: dict = {}
            for _ln in _split_log.read_text('utf-8', errors='ignore').strip().splitlines():
                try:
                    _ev = _json.loads(_ln)
                    for _ch in _ev.get('child_stems', []):
                        _lin_map[_ch] = {
                            'parent': _ev.get('parent_stem', ''),
                            'siblings': [s for s in _ev.get('child_stems', []) if s != _ch],
                        }
                except Exception:
                    pass
            if stem in _lin_map:
                _l = _lin_map[stem]
                _lineage_ctx = (
                    f"\nSPLIT LINEAGE: this file was born from '{_l['parent']}'. "
                    f"Its numeric encoding starts at zero — it must re-earn its routing weights. "
                    f"Siblings that handle other concerns: {', '.join(_l['siblings'][:4]) or 'none'}. "
                    f"Do NOT duplicate logic that belongs to siblings."
                )
    except Exception:
        pass

    user_prompt = f"""INTENT: {intent}{_lineage_ctx}

FILE: {fpath.name}
SOURCE:
```python
{source_trunc}
```

Apply the minimal surgical fix. Output only search-replace blocks."""

    if dry_run:
        return {'success': True, 'dry_run': True, 'reason': 'dry-run — no write',
                'file': str(fpath.relative_to(ROOT))}

    completion = _call_deepseek(_COMPILE_SYSTEM, user_prompt, api_key, max_tokens=1500)
    if not completion:
        return {'success': False, 'reason': 'deepseek returned empty'}

    if 'NO_CHANGES' in completion.upper()[:30]:
        return {'success': True, 'reason': 'deepseek: NO_CHANGES needed',
                'file': str(fpath.relative_to(ROOT))}

    # delegate to file_overwriter's apply machinery
    fo_mod = _load_glob_module('src', 'file_overwriter_seq001*')
    if fo_mod and hasattr(fo_mod, 'overwrite_file'):
        try:
            result = fo_mod.overwrite_file(stem, intent, dry_run=False, _patch_override=completion)
            return {
                'success': result.get('applied', False),
                'reason': result.get('error', 'applied' if result.get('applied') else 'not applied'),
                'file': str(fpath.relative_to(ROOT)),
                'diff_preview': result.get('diff', '')[:200],
            }
        except TypeError:
            # _patch_override not supported yet — fall back to direct apply
            pass

    # Direct apply fallback — parse blocks ourselves
    blocks = _parse_search_replace(completion)
    if not blocks:
        return {'success': False, 'reason': 'no valid search-replace blocks in completion',
                'completion_preview': completion[:200]}

    patched = source
    applied = 0
    for search, replace in blocks:
        if search in patched:
            patched = patched.replace(search, replace, 1)
            applied += 1

    if applied == 0:
        return {'success': False, 'reason': 'search blocks did not match file content',
                'file': str(fpath.relative_to(ROOT))}

    # backup + atomic write
    import shutil, tempfile
    backup_dir = LOGS / 'file_overwrite_backups' / stem
    backup_dir.mkdir(parents=True, exist_ok=True)
    ts_str = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')
    shutil.copy2(fpath, backup_dir / f'{ts_str}.py.bak')

    try:
        fd, tmp = tempfile.mkstemp(dir=fpath.parent, suffix='.tmp')
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(patched)
        os.replace(tmp, fpath)
    except Exception as e:
        return {'success': False, 'reason': f'write failed: {e}',
                'file': str(fpath.relative_to(ROOT))}

    return {
        'success': True,
        'reason': f'applied {applied} block(s)',
        'file': str(fpath.relative_to(ROOT)),
        'blocks_applied': applied,
    }


def _parse_search_replace(completion: str) -> list[tuple[str, str]]:
    """Extract (search, replace) pairs from <<<SEARCH/===/>>>REPLACE format."""
    blocks = []
    parts = completion.split('<<<SEARCH')
    for part in parts[1:]:
        if '===' not in part or '>>>REPLACE' not in part:
            continue
        try:
            search_part, rest = part.split('===', 1)
            replace_part = rest.split('>>>REPLACE', 1)[0]
            search = search_part.strip('\n')
            replace = replace_part.strip('\n')
            if search:
                blocks.append((search, replace))
        except Exception:
            continue
    return blocks


# ── main daemon loop ───────────────────────────────────────────────────────────

def run_cycle(api_key: str, dry_run: bool, already_attempted: set[str]) -> int:
    """Run one work cycle. Returns number of items processed."""
    processed = 0

    # collect work by priority
    work_items = []
    work_items.extend(_rejected_patch_work(already_attempted))      # retries first
    work_items.extend(_pigeon_compliance_work(already_attempted))   # then compliance
    work_items.extend(_intent_work(already_attempted))              # then intents

    if not work_items:
        print('[daemon] no work this cycle')
        return 0

    # process first available item
    item = work_items[0]
    already_attempted.add(item['key'])
    print(f'[daemon] → {item["type"]} stem={item["stem"]} intent={item["intent"][:60]!r}')

    result = _do_fix(item, api_key, dry_run)
    result['stem'] = item['stem']
    result['action'] = item['type']

    _log({
        **result,
        'work_type': item['type'],
        'bug': item.get('bug', ''),
        'intent_preview': item['intent'][:100],
    })

    processed += 1
    return processed


def main():
    p = argparse.ArgumentParser(description='deepseek_daemon — always-on parallel fixer')
    p.add_argument('--dry-run', action='store_true', help='no writes — analysis only')
    p.add_argument('--once', action='store_true', help='single cycle then exit')
    p.add_argument('--cycle-s', type=int, default=CYCLE_S, help='seconds between cycles')
    args = p.parse_args()

    api_key = _load_api_key()
    if not api_key:
        print('[daemon] ERROR: DEEPSEEK_API_KEY not found in env or .env')
        return 1

    print(f'[daemon] starting — cycle={args.cycle_s}s dry_run={args.dry_run}')
    _log({'action': 'start', 'stem': 'daemon', 'result': f'cycle={args.cycle_s}s dry_run={args.dry_run}', 'dry_run': args.dry_run})

    already_attempted: set[str] = set()

    while True:
        try:
            n = run_cycle(api_key, args.dry_run, already_attempted)
            print(f'[daemon] cycle done — processed={n} attempted={len(already_attempted)}')
        except Exception as e:
            print(f'[daemon] cycle error: {e}')
            _log({'action': 'cycle_error', 'stem': 'daemon', 'result': str(e)[:120]})

        if args.once:
            break
        time.sleep(args.cycle_s)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
