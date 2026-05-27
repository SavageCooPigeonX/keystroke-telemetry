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

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.local_env_loader_seq001_v001 import load_local_env

ROOT = Path(__file__).parent.parent
LOGS = ROOT / 'logs'
DAEMON_LOG = LOGS / 'deepseek_daemon.jsonl'
INTENT_JOBS = LOGS / 'intent_jobs.jsonl'
PROMPT_JOBS = LOGS / 'deepseek_prompt_jobs.jsonl'
PROMPT_RESULTS = LOGS / 'deepseek_prompt_results.jsonl'
CODE_COMPLETION_JOBS = LOGS / 'deepseek_code_completion_jobs.jsonl'
ARTIFACT_LOG = LOGS / 'deepseek_artifact_writes.jsonl'
OVERWRITE_LOG = LOGS / 'file_overwrites.jsonl'
POST_GRADE_LOG = LOGS / 'post_patch_grades.jsonl'

CYCLE_S = 12            # minimum seconds between DeepSeek calls
MAX_GRADE_RETRY = 2     # max retries for a rejected patch
INTENT_MIN_GRADE = 0.1  # minimum sim grade to attempt a fix

_DEEPSEEK_URL = 'https://api.deepseek.com/v1/chat/completions'
_DEEPSEEK_MODEL = os.environ.get('DEEPSEEK_CODING_MODEL') or os.environ.get('DEEPSEEK_MODEL') or 'deepseek-v4-pro'
_DEEPSEEK_FAST_MODEL = os.environ.get('DEEPSEEK_FAST_MODEL') or 'deepseek-v4-flash'
_AUTONOMOUS_PROMPT_WRITES = os.environ.get('DEEPSEEK_AUTONOMOUS_PROMPT_WRITES', '').lower() in ('1', 'true', 'yes')
_ARTIFACT_ROOTS = ('logs/deepseek_artifacts', 'docs/research', 'docs/deepseek_artifacts')


# ── helpers ────────────────────────────────────────────────────────────────────

def _load_api_key() -> str | None:
    load_local_env(ROOT)
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


def _call_deepseek(system: str, user: str, api_key: str, max_tokens: int = 2000, model: str | None = None) -> str | None:
    import urllib.request
    body = json.dumps({
        'model': model or _DEEPSEEK_MODEL,
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


def _prompt_max_tokens(job: dict, model: str) -> int:
    explicit = job.get('max_tokens')
    if explicit is not None:
        try:
            return max(256, int(explicit))
        except (TypeError, ValueError):
            pass
    mode = str(job.get('mode') or '').lower()
    reasoning_model = any(token in str(model).lower() for token in ('v4', 'reasoner', 'r1'))
    if mode in {'research_md_artifact', 'meta_analysis_artifact'}:
        return 8000 if reasoning_model else 4500
    return 6000 if reasoning_model else 2400


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
        grades = job.get('grades', {})
        top_files = job.get('top_files', [])
        intent = job.get('intent_text', '')
        if not intent or not top_files:
            continue
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


def _done_prompt_job_ids() -> set[str]:
    done: set[str] = set()
    for row in _read_jsonl(PROMPT_RESULTS):
        if row.get('dry_run'):
            continue
        jid = row.get('job_id')
        if jid:
            done.add(str(jid))
    return done


def _stem_from_focus(focus_files: list) -> str:
    for item in focus_files:
        name = item.get('name') if isinstance(item, dict) else str(item)
        if not name:
            continue
        name = str(name).replace('\\', '/')
        if name.startswith('logs/'):
            continue
        p = Path(name)
        if p.suffix == '.py':
            return p.stem
        if '/' not in name and '.' not in name:
            return name
    return ''


def _prompt_job_work(already_attempted: set[str]) -> list[dict]:
    """Pull prompt-triggered DeepSeek V4 jobs queued by codex_compat."""
    jobs = _read_jsonl(PROMPT_JOBS)
    if not jobs:
        return []
    done = _done_prompt_job_ids()
    target_job_id = os.environ.get('PIGEON_DEEPSEEK_TARGET_JOB_ID', '').strip()
    work = []
    for job in reversed(jobs):
        jid = str(job.get('job_id') or '')
        if not jid or jid in done:
            continue
        if target_job_id and jid != target_job_id:
            continue
        key = f'prompt:{jid}'
        if key in already_attempted:
            continue
        prompt = str(job.get('prompt') or '').strip()
        if not prompt:
            continue
        focus = job.get('focus_files') if isinstance(job.get('focus_files'), list) else []
        work.append({
            'type': 'prompt_coding_context',
            'stem': _stem_from_focus(focus),
            'intent': prompt,
            'job': job,
            'key': key,
            'priority': _job_priority(job),
        })
    work.sort(key=lambda item: item.get('priority', 5))
    return work[:3]


def _job_priority(job: dict) -> int:
    value = job.get('priority')
    if value is None or value == '':
        return 5
    try:
        return int(value)
    except (TypeError, ValueError):
        return 5


# ── DeepSeek actions ───────────────────────────────────────────────────────────

def _code_completion_job_work(already_attempted: set[str]) -> list[dict]:
    """Pull file-sim DeepSeek completion jobs into the prompt-result lane."""
    if os.environ.get('PIGEON_DEEPSEEK_TARGET_JOB_ID', '').strip():
        return []
    jobs = _read_jsonl(CODE_COMPLETION_JOBS)
    if not jobs:
        return []
    done = _done_prompt_job_ids()
    work = []
    for job in reversed(jobs):
        jid = str(job.get('job_id') or '')
        if not jid or jid in done:
            continue
        key = f'code_completion:{jid}'
        if key in already_attempted:
            continue
        prompt = str(job.get('prompt') or '').strip()
        if not prompt:
            continue
        focus = list(job.get('context_injection') or [])
        file_name = str(job.get('file') or '')
        if file_name:
            focus.insert(0, file_name)
        work.append({
            'type': 'prompt_coding_context',
            'stem': Path(file_name).stem or _stem_from_focus(focus),
            'intent': prompt,
            'job': {
                'job_id': jid,
                'prompt': prompt,
                'focus_files': focus,
                'model': job.get('model') or _DEEPSEEK_MODEL,
                'context_confidence': (job.get('ten_q') or {}).get('score', 0),
                'context_pack_path': 'logs/file_job_council_latest.json',
                'autonomous_write': False,
            },
            'key': key,
            'priority': 2,
        })
    return work[:3]


_COMPILE_SYSTEM = """You are the DeepSeek compiler for a Python codebase that uses the Pigeon naming system.

Your job: surgically fix the stated bug or implement the stated intent in the target file.
You have full awareness of pigeon code compliance rules:
- Files must not hardcode sibling imports — use glob-based dynamic load: `_load_glob_module(root, 'src', 'stem_pattern*')`
- Files over the active PIGEON_MAX line cap get decomposed — identify the natural boundary if over cap
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


_PROMPT_SYSTEM = """You are DeepSeek V4 Pro acting as the coding delegate for this repo.
Use the dynamic context pack, prompt text, deleted words, focus files, and recent state.
Return a compact engineering response:
1. Which file(s) should be touched first.
2. The minimal coding action.
3. Any risk or missing input.
If code changes are needed, include surgical search-replace blocks only after the plan.
Do not invent stale observatory facts; prefer the provided live context."""


def _focus_source_snippets(focus_files: list, limit: int = 3) -> str:
    snippets: list[str] = []
    for item in focus_files[:limit * 2]:
        name = item.get('name') if isinstance(item, dict) else str(item)
        if not name:
            continue
        candidates: list[Path] = []
        p = ROOT / str(name)
        if p.exists() and p.is_file():
            candidates.append(p)
        stem = Path(str(name)).stem if str(name).endswith('.py') else str(name)
        for folder in ('src', 'client', 'pigeon_compiler'):
            candidates.extend(sorted((ROOT / folder).glob(f'{stem}*.py'))[:1])
        for candidate in candidates:
            try:
                rel = candidate.relative_to(ROOT)
                source = candidate.read_text('utf-8', errors='ignore')
            except Exception:
                continue
            lines = source.splitlines()
            body = '\n'.join(lines[:220])
            if len(lines) > 220:
                body += f'\n# ... {len(lines) - 220} more lines truncated'
            snippets.append(f'FILE: {rel}\n```python\n{body}\n```')
            break
        if len(snippets) >= limit:
            break
    return '\n\n'.join(snippets)


def _do_prompt_job(work: dict, api_key: str, dry_run: bool) -> dict:
    job = work.get('job') or {}
    prompt = str(job.get('prompt') or work.get('intent') or '').strip()
    job_id = str(job.get('job_id') or work.get('key') or '')
    focus_files = job.get('focus_files') if isinstance(job.get('focus_files'), list) else []
    model = str(job.get('model') or _DEEPSEEK_MODEL)
    autonomous_write = bool(job.get('autonomous_write')) or _AUTONOMOUS_PROMPT_WRITES

    if dry_run:
        result = {
            'success': True,
            'dry_run': True,
            'reason': 'prompt job queued; dry-run skipped API call',
            'job_id': job_id,
            'model': model,
        }
        _append_prompt_result(result)
        return result

    if autonomous_write and work.get('stem'):
        result = _do_fix({
            'type': 'prompt_coding',
            'stem': work['stem'],
            'path': _first_focus_python_path(focus_files),
            'intent': prompt,
            'key': work['key'],
        }, api_key, dry_run=False)
        result.update({'job_id': job_id, 'model': model, 'autonomous_write': True})
        _append_prompt_result(result)
        return result

    pack_path = ROOT / str(job.get('context_pack_path') or 'logs/dynamic_context_pack.json')
    context_pack = {}
    if pack_path.exists():
        try:
            context_pack = json.loads(pack_path.read_text('utf-8', errors='ignore'))
        except Exception:
            context_pack = {}
    snippets = _focus_source_snippets(focus_files)
    user = f"""PROMPT:
{prompt}

DELETED WORDS: {', '.join(job.get('deleted_words', [])[:12]) or 'none'}
CONTEXT CONFIDENCE: {job.get('context_confidence', 0)}

DYNAMIC CONTEXT PACK:
{json.dumps(context_pack, ensure_ascii=False, indent=2)[:6000]}

FOCUS SOURCE:
{snippets or '(no source snippets resolved)'}
"""
    max_tokens = _prompt_max_tokens(job, model)
    completion = _call_deepseek(_PROMPT_SYSTEM, user, api_key, max_tokens=max_tokens, model=model)
    artifact = (
        _write_prompt_artifact(job, completion or '')
        if completion and _should_write_artifact(job)
        else {'status': 'skipped', 'reason': 'artifact_not_requested'}
    )
    result = {
        'success': bool(completion),
        'reason': 'deepseek prompt context completed' if completion else 'deepseek returned empty',
        'job_id': job_id,
        'model': model,
        'prompt_preview': prompt[:180],
        'focus_files': focus_files[:8],
        'completion': (completion or '')[:6000],
        'autonomous_write': False,
        'artifact': artifact,
        'artifact_written': artifact.get('status') == 'written',
        'max_tokens': max_tokens,
    }
    _append_prompt_result(result)
    return result


def _append_prompt_result(result: dict) -> None:
    result = {**result, 'ts': datetime.now(timezone.utc).isoformat()}
    PROMPT_RESULTS.parent.mkdir(parents=True, exist_ok=True)
    with open(PROMPT_RESULTS, 'a', encoding='utf-8') as f:
        f.write(json.dumps(result, ensure_ascii=False) + '\n')
    (LOGS / 'deepseek_prompt_latest_result.json').write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )


def _should_write_artifact(job: dict) -> bool:
    mode = str(job.get('mode') or '').lower()
    return bool(job.get('write_artifact') or job.get('artifact_path') or mode in {
        'research_md_artifact',
        'meta_analysis_artifact',
    })


def _write_prompt_artifact(job: dict, completion: str) -> dict:
    path_result = _safe_artifact_path(str(job.get('artifact_path') or ''))
    if path_result.get('status') != 'ok':
        return path_result
    target = Path(path_result['path'])
    target.parent.mkdir(parents=True, exist_ok=True)
    text = _artifact_markdown(job, completion)
    target.write_text(text, encoding='utf-8')
    record = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'job_id': job.get('job_id'),
        'artifact_path': str(target.relative_to(ROOT)).replace('\\', '/'),
        'chars': len(text),
        'mode': job.get('mode'),
        'source': job.get('source'),
    }
    ARTIFACT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with ARTIFACT_LOG.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')
    return {'status': 'written', **record}


def _safe_artifact_path(raw_path: str) -> dict:
    rel = raw_path.strip().replace('\\', '/')
    if not rel:
        return {'status': 'blocked', 'reason': 'missing_artifact_path'}
    if rel.startswith('/') or re_has_drive(rel) or '..' in Path(rel).parts:
        return {'status': 'blocked', 'reason': 'artifact_path_must_be_repo_relative'}
    if Path(rel).suffix.lower() != '.md':
        return {'status': 'blocked', 'reason': 'only_markdown_artifacts_allowed'}
    target = (ROOT / rel).resolve()
    root_resolved = ROOT.resolve()
    try:
        target.relative_to(root_resolved)
    except ValueError:
        return {'status': 'blocked', 'reason': 'artifact_path_outside_repo'}
    allowed = False
    for prefix in _ARTIFACT_ROOTS:
        try:
            target.relative_to((ROOT / prefix).resolve())
            allowed = True
            break
        except ValueError:
            continue
    if not allowed:
        return {'status': 'blocked', 'reason': f'artifact_path_must_start_with:{",".join(_ARTIFACT_ROOTS)}'}
    return {'status': 'ok', 'path': str(target)}


def re_has_drive(path_text: str) -> bool:
    return len(path_text) >= 2 and path_text[1] == ':'


def _artifact_markdown(job: dict, completion: str) -> str:
    text = _strip_markdown_fence(str(completion or '').strip())
    header = [
        '<!-- deepseek-artifact',
        f"job_id: {job.get('job_id')}",
        f"mode: {job.get('mode')}",
        f"generated_at: {datetime.now(timezone.utc).isoformat()}",
        '-->',
        '',
    ]
    return '\n'.join(header) + text[:100000].rstrip() + '\n'


def _strip_markdown_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith('```'):
        lines = stripped.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == '```':
            return '\n'.join(lines[1:-1]).strip()
    return stripped


def _work_type_rank(work_type: str) -> int:
    if work_type == 'prompt_coding_context':
        return 0
    if work_type == 'retry_rejected':
        return 1
    if work_type == 'pigeon_compliance':
        return 2
    if work_type == 'intent':
        return 3
    return 9


def _do_fix(work: dict, api_key: str, dry_run: bool) -> dict:
    """Run one DeepSeek fix cycle for a work item. Returns result dict."""
    stem = work['stem']
    intent = work['intent']
    work_type = work['type']

    # find the file
    fpath = _resolve_work_path(work)
    if not fpath:
        return {'success': False, 'reason': f'file not found for stem {stem}'}

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
        return {'success': False, 'reason': 'deepseek returned empty',
                'file': str(fpath.relative_to(ROOT))}

    if 'NO_CHANGES' in completion.upper()[:30]:
        return {'success': True, 'reason': 'deepseek: NO_CHANGES needed',
                'file': str(fpath.relative_to(ROOT))}

    # delegate to file_overwriter's apply machinery
    fo_mod = _load_glob_module('src', 'file_overwriter_seq001*')
    if fo_mod and hasattr(fo_mod, 'overwrite_file'):
        try:
            result = fo_mod.overwrite_file(
                stem,
                intent,
                grade_result={'confidence': 1.0, 'approved': True},
                dry_run=False,
                approved=True,
                target_path=str(fpath.relative_to(ROOT)).replace('\\', '/'),
                _patch_override=completion,
            )
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


def _first_focus_python_path(focus_files: list) -> str:
    for item in focus_files:
        name = item.get('name') if isinstance(item, dict) else str(item)
        name = str(name or '').replace('\\', '/')
        if name.endswith('.py'):
            return name
    return ''


def _safe_repo_file(raw_path: str) -> Path | None:
    rel = str(raw_path or '').strip().replace('\\', '/')
    if not rel or rel.startswith('/') or re_has_drive(rel) or '..' in Path(rel).parts:
        return None
    candidate = (ROOT / rel).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        return None
    if candidate.exists() and candidate.is_file() and candidate.suffix == '.py':
        return candidate
    return None


def _resolve_work_path(work: dict) -> Path | None:
    explicit = _safe_repo_file(str(work.get('path') or work.get('file') or ''))
    if explicit:
        return explicit

    stem = str(work.get('stem') or '')
    src_matches = sorted((ROOT / 'src').glob(f'{stem}*.py'))
    if not src_matches:
        for folder in ['pigeon_compiler', 'pigeon_compiler/git_plugin', 'client']:
            src_matches = sorted((ROOT / folder).glob(f'{stem}*.py'))
            if src_matches:
                break
    return src_matches[-1] if src_matches else None


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
    work_items.extend(_prompt_job_work(already_attempted))          # live prompts / artifact packets
    work_items.extend(_code_completion_job_work(already_attempted)) # file-sim DeepSeek drafts
    work_items.extend(_rejected_patch_work(already_attempted))      # retries first
    work_items.extend(_pigeon_compliance_work(already_attempted))   # then compliance
    work_items.extend(_intent_work(already_attempted))              # then intents
    work_items.sort(key=lambda item: (_job_priority(item), _work_type_rank(str(item.get('type') or ''))))

    if not work_items:
        print('[daemon] no work this cycle')
        return 0

    # process first available item
    item = work_items[0]
    already_attempted.add(item['key'])
    print(f'[daemon] -> {item["type"]} stem={item["stem"]} intent={item["intent"][:60]!r}')

    if item['type'] == 'prompt_coding_context':
        result = _do_prompt_job(item, api_key, dry_run)
    else:
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
    if not api_key and not args.dry_run:
        print('[daemon] ERROR: DEEPSEEK_API_KEY not found in env or .env')
        return 1
    if not api_key:
        api_key = 'dry-run'

    print(f'[daemon] starting - model={_DEEPSEEK_MODEL} fast={_DEEPSEEK_FAST_MODEL} cycle={args.cycle_s}s dry_run={args.dry_run}')
    _log({
        'action': 'start',
        'stem': 'daemon',
        'result': f'model={_DEEPSEEK_MODEL} fast={_DEEPSEEK_FAST_MODEL} cycle={args.cycle_s}s dry_run={args.dry_run}',
        'dry_run': args.dry_run,
        'model': _DEEPSEEK_MODEL,
        'fast_model': _DEEPSEEK_FAST_MODEL,
    })

    already_attempted: set[str] = set()

    while True:
        try:
            n = run_cycle(api_key, args.dry_run, already_attempted)
            print(f'[daemon] cycle done - processed={n} attempted={len(already_attempted)}')
        except Exception as e:
            print(f'[daemon] cycle error: {e}')
            _log({'action': 'cycle_error', 'stem': 'daemon', 'result': str(e)[:120]})

        if args.once:
            break
        time.sleep(args.cycle_s)

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
