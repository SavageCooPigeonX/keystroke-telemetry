"""
Intent Reconstructor — strict verification for recent operator intent backlog.

Scans the last 100 operator prompts, synchronizes unresolved intents into the
task queue, and injects a managed prompt block that tells Copilot whether it is
allowed to stop.

Zero LLM calls — pure signal processing from existing telemetry.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


JOURNAL_PATH = 'logs/prompt_journal.jsonl'
HEAT_MAP_PATH = 'file_heat_map.json'
TASK_QUEUE_PATH = 'task_queue.json'
SNAPSHOT_PATH = 'logs/intent_backlog_latest.json'
RESOLUTION_PATH = 'intent_backlog_resolutions.json'
COPILOT_PATH = '.github/copilot-instructions.md'
BLOCK_START = '<!-- pigeon:intent-backlog -->'
BLOCK_END = '<!-- /pigeon:intent-backlog -->'

MAX_PROMPTS = 100
MAX_VISIBLE_INTENTS = 8
MAX_STORED_INTENTS = 20
MIN_CHARS_FOR_INTENT = 20
ABANDONMENT_THRESHOLD = 0.3
DAYS_COLD = 2
QUEUE_SOURCE = 'intent_reconstructor'
UNRESOLVED_STATUSES = {'abandoned', 'partial', 'cold'}
_QUEUE_EMPTY = {'tasks': [], 'next_id': 1}


def _normalize_text(value: str) -> str:
    return re.sub(r'\s+', ' ', str(value)).strip().lower()


def _slug(value: str, limit: int = 72) -> str:
    text = re.sub(r'[^a-z0-9]+', '-', _normalize_text(value))
    return text.strip('-')[:limit] or 'prompt'


def _is_operator_prompt(prompt: dict) -> bool:
    if prompt.get('prompt_kind') == 'meta_hook':
        return False
    if prompt.get('intent') in {'file_chat', 'file_wake'}:
        return False
    if prompt.get('source') == 'profile_chat_server':
        return False
    return bool(str(prompt.get('msg', '')).strip())


def _load_prompts(root: Path, n: int = MAX_PROMPTS) -> list[dict]:
    path = root / JOURNAL_PATH
    if not path.exists():
        return []
    prompts = []
    for line in reversed(path.read_text('utf-8', errors='ignore').splitlines()):
        try:
            prompt = json.loads(line)
        except Exception:
            continue
        if not _is_operator_prompt(prompt):
            continue
        prompts.append(prompt)
        if len(prompts) >= n:
            break
    prompts.reverse()
    return prompts


def _load_heat_map(root: Path) -> dict[str, Any]:
    path = root / HEAT_MAP_PATH
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text('utf-8'))
    except Exception:
        return {}


def _load_task_queue(root: Path) -> dict[str, Any]:
    path = root / TASK_QUEUE_PATH
    if not path.exists():
        return dict(_QUEUE_EMPTY)
    try:
        return json.loads(path.read_text('utf-8'))
    except Exception:
        return dict(_QUEUE_EMPTY)


def _save_task_queue(root: Path, queue: dict[str, Any]) -> None:
    (root / TASK_QUEUE_PATH).write_text(
        json.dumps(queue, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )


def _load_resolution_map(root: Path) -> dict[str, dict[str, Any]]:
    path = root / RESOLUTION_PATH
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text('utf-8'))
    except Exception:
        return {}

    entries = payload.get('entries', {})
    if isinstance(entries, list):
        normalized = {}
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            source_key = str(entry.get('source_key', '')).strip()
            if source_key:
                normalized[source_key] = entry
        return normalized

    if not isinstance(entries, dict):
        return {}

    return {
        str(source_key): entry
        for source_key, entry in entries.items()
        if isinstance(entry, dict)
    }


def _intent_source_key(prompt: dict, msg: str) -> str:
    ts = str(prompt.get('ts', '')).strip()
    if ts:
        return f'intent_backlog:{ts}'
    return f'intent_backlog:{_slug(msg, 96)}'


def extract_intent_signals(prompt: dict) -> dict[str, Any]:
    msg = str(prompt.get('msg', '')).strip()
    signals = prompt.get('signals', {})
    return {
        'ts': prompt.get('ts', ''),
        'msg': msg,
        'msg_preview': msg[:100] if len(msg) > 100 else msg,
        'source_key': _intent_source_key(prompt, msg),
        'intent': prompt.get('intent', 'unknown'),
        'state': prompt.get('cognitive_state', 'unknown'),
        'deletion_ratio': signals.get('deletion_ratio', 0),
        'wpm': signals.get('wpm', 0),
        'hesitation': signals.get('hesitation_count', 0),
        'deleted_words': prompt.get('deleted_words', []),
        'module_refs': prompt.get('module_refs', []),
        'files_open': prompt.get('files_open', []),
    }


def get_intent_verification(signal: dict, heat_map: dict[str, Any]) -> dict[str, Any]:
    refs = {
        _normalize_text(item)
        for item in signal.get('module_refs', [])
        if str(item).strip()
    }
    files = {
        _normalize_text(item)
        for item in signal.get('files_open', [])
        if str(item).strip()
    }
    touched = refs | files
    matched_targets = []
    recently_touched = False

    for file_name, data in heat_map.items():
        norm_file = _normalize_text(file_name)
        if touched and not any(target and target in norm_file for target in touched):
            continue
        if touched:
            matched_targets.append(file_name)
        last_touch = data.get('last_touch', '')
        if not last_touch:
            continue
        try:
            touch_dt = datetime.fromisoformat(last_touch.replace('Z', '+00:00'))
        except Exception:
            continue
        if datetime.now(timezone.utc) - touch_dt < timedelta(days=DAYS_COLD):
            recently_touched = True
            break

    if recently_touched:
        return {
            'status': 'fulfilled',
            'verification_reason': 'recent_file_activity',
            'matched_targets': matched_targets[:5],
        }

    deletion_ratio = float(signal.get('deletion_ratio', 0) or 0)
    if deletion_ratio > ABANDONMENT_THRESHOLD:
        return {
            'status': 'abandoned',
            'verification_reason': 'high_deletion_ratio',
            'matched_targets': matched_targets[:5],
        }

    if signal.get('state') == 'abandoned':
        return {
            'status': 'abandoned',
            'verification_reason': 'operator_abandoned_state',
            'matched_targets': matched_targets[:5],
        }

    if signal.get('deleted_words'):
        return {
            'status': 'partial',
            'verification_reason': 'deleted_words_left_unresolved',
            'matched_targets': matched_targets[:5],
        }

    ts = str(signal.get('ts', '')).strip()
    if ts:
        try:
            prompt_dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
        except Exception:
            prompt_dt = None
        if prompt_dt and datetime.now(timezone.utc) - prompt_dt > timedelta(days=DAYS_COLD):
            return {
                'status': 'cold',
                'verification_reason': 'no_recent_follow_through',
                'matched_targets': matched_targets[:5],
            }

    return {
        'status': 'active',
        'verification_reason': 'recent_operator_prompt',
        'matched_targets': matched_targets[:5],
    }


def classify_intent_status(signal: dict, heat_map: dict[str, Any]) -> str:
    return get_intent_verification(signal, heat_map)['status']


def _build_reconstructed_text(msg: str, deleted_words: list[str]) -> str:
    if deleted_words:
        return f"{msg[:80]}... (also considered: {' '.join(deleted_words[:5])})"
    return msg[:120]


def reconstruct_abandoned_intents(root: Path, prompt_limit: int = MAX_PROMPTS) -> list[dict[str, Any]]:
    prompts = _load_prompts(root, prompt_limit)
    heat_map = _load_heat_map(root)
    unresolved = []

    for prompt in prompts:
        msg = str(prompt.get('msg', '')).strip()
        if len(msg) < MIN_CHARS_FOR_INTENT:
            continue
        signal = extract_intent_signals(prompt)
        deleted_words = [
            item.get('word', item) if isinstance(item, dict) else str(item)
            for item in signal.get('deleted_words', [])
        ]
        verification = get_intent_verification(signal, heat_map)
        if verification['status'] not in UNRESOLVED_STATUSES:
            continue
        unresolved.append({
            **signal,
            **verification,
            'deleted_words': deleted_words,
            'original_msg': msg[:200],
            'reconstructed': _build_reconstructed_text(msg, deleted_words),
            'confidence': max(0.0, 1.0 - float(signal.get('deletion_ratio', 0) or 0)),
        })

    return _dedupe_intents(unresolved)


def _dedupe_intents(intents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not intents:
        return []
    deduped = []
    seen = set()
    for intent in reversed(intents):
        key = _slug(intent['original_msg'], 64)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(intent)
    deduped.reverse()
    return deduped[:MAX_STORED_INTENTS]


def generate_tasks_from_intents(intents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tasks = []
    stage_by_status = {'abandoned': 'revisit', 'partial': 'complete', 'cold': 'verify'}
    priority_by_status = {'abandoned': 'high', 'partial': 'medium', 'cold': 'medium'}
    for index, intent in enumerate(intents, start=1):
        focus = [
            str(item) for item in (intent.get('files_open') or intent.get('module_refs') or [])
            if str(item).strip()
        ]
        tasks.append({
            'local_id': f'ir-{index:03d}',
            'title': intent['reconstructed'][:60] + ('...' if len(intent['reconstructed']) > 60 else ''),
            'intent': intent['reconstructed'],
            'stage': stage_by_status[intent['status']],
            'priority': priority_by_status[intent['status']],
            'source': QUEUE_SOURCE,
            'source_key': intent['source_key'],
            'original_ts': intent['ts'],
            'focus_files': focus[:3],
            'confidence': intent['confidence'],
            'verification_reason': intent['verification_reason'],
            'status': intent['status'],
        })
    return tasks


def get_reconstruction_summary(
    root: Path,
    prompt_limit: int = MAX_PROMPTS,
    intents: list[dict[str, Any]] | None = None,
    scanned_prompts: int | None = None,
) -> dict[str, Any]:
    if intents is None:
        intents = reconstruct_abandoned_intents(root, prompt_limit)
    if scanned_prompts is None:
        scanned_prompts = len(_load_prompts(root, prompt_limit))

    counts = defaultdict(int)
    for intent in intents:
        counts[intent['status']] += 1

    return {
        'prompt_limit': prompt_limit,
        'scanned_prompts': scanned_prompts,
        'strict_verification': True,
        'total': len(intents),
        'unresolved_count': len(intents),
        'abandoned': counts['abandoned'],
        'partial': counts['partial'],
        'cold': counts['cold'],
        'intents': intents,
    }


def synchronize_intent_backlog(root: Path, prompt_limit: int = MAX_PROMPTS) -> dict[str, Any]:
    root = Path(root)
    prompts = _load_prompts(root, prompt_limit)
    intents = reconstruct_abandoned_intents(root, prompt_limit)
    resolutions = _load_resolution_map(root)
    resolved_keys = {
        source_key
        for source_key, entry in resolutions.items()
        if str(entry.get('status', '')).strip().lower() == 'resolved'
    }
    active_intents = [
        intent for intent in intents
        if intent['source_key'] not in resolved_keys
    ]
    queue = _load_task_queue(root)
    tasks = queue.setdefault('tasks', [])
    queue['next_id'] = int(queue.get('next_id', 1) or 1)
    now = datetime.now(timezone.utc).isoformat()

    existing = {
        task.get('source_key'): task
        for task in tasks
        if task.get('source') == QUEUE_SOURCE and task.get('source_key')
    }
    task_id_by_source_key = {}
    active_keys = set()
    created = 0
    reopened = 0
    verified = 0
    carried = 0

    for seed in generate_tasks_from_intents(intents):
        source_key = seed['source_key']
        resolution = resolutions.get(source_key, {})
        active_keys.add(source_key)
        task = existing.get(source_key)

        if source_key in resolved_keys:
            active_keys.discard(source_key)
            resolution_ts = str(resolution.get('verified_ts') or now)
            if task is None:
                task = {
                    'id': f"tq-{queue['next_id']:03d}",
                    'status': 'done',
                    'created_ts': resolution_ts,
                    'completed_ts': resolution_ts,
                    'commit': 'verified:intent-resolution',
                }
                queue['next_id'] += 1
                tasks.append(task)
                created += 1
            elif task.get('status') != 'done':
                task['status'] = 'done'
                task['completed_ts'] = resolution_ts
                task['commit'] = 'verified:intent-resolution'
                verified += 1

            task.update({
                'title': seed['title'],
                'intent': seed['intent'],
                'stage': seed['stage'],
                'focus_files': seed['focus_files'],
                'source': QUEUE_SOURCE,
                'source_key': seed['source_key'],
                'priority': seed['priority'],
                'confidence': seed['confidence'],
                'original_ts': seed['original_ts'],
                'manifest_ref': resolution.get('manifest_ref', RESOLUTION_PATH),
                'verification_state': 'verified_done',
                'verification_reason': resolution.get('outcome', 'verified_resolution_artifact'),
                'verification_summary': resolution.get('summary', ''),
                'last_verified_ts': resolution_ts,
                'backlog_prompt_limit': prompt_limit,
            })
            task_id_by_source_key[source_key] = task['id']
            continue

        if task is None:
            task = {
                'id': f"tq-{queue['next_id']:03d}",
                'status': 'pending',
                'created_ts': now,
                'completed_ts': None,
                'commit': None,
            }
            queue['next_id'] += 1
            tasks.append(task)
            created += 1
        elif task.get('status') == 'done':
            task['status'] = 'pending'
            task['completed_ts'] = None
            task['commit'] = None
            task['reopened_ts'] = now
            reopened += 1
        else:
            carried += 1

        task.update({
            'title': seed['title'],
            'intent': seed['intent'],
            'stage': seed['stage'],
            'focus_files': seed['focus_files'],
            'source': QUEUE_SOURCE,
            'source_key': seed['source_key'],
            'priority': seed['priority'],
            'confidence': seed['confidence'],
            'original_ts': seed['original_ts'],
            'verification_state': 'unresolved',
            'verification_reason': seed['verification_reason'],
            'last_verified_ts': now,
            'backlog_prompt_limit': prompt_limit,
        })
        task_id_by_source_key[source_key] = task['id']

    for task in tasks:
        if task.get('source') != QUEUE_SOURCE:
            continue
        if task.get('source_key') in resolved_keys:
            continue
        if task.get('source_key') in active_keys:
            continue
        if task.get('status') != 'done':
            task['status'] = 'done'
            task['completed_ts'] = now
            task['commit'] = 'verified:intent-backlog'
            verified += 1
        task['verification_state'] = 'verified_done'
        task['verification_reason'] = 'cleared_from_backlog'
        task['last_verified_ts'] = now

    _save_task_queue(root, queue)

    summary = get_reconstruction_summary(
        root,
        prompt_limit=prompt_limit,
        intents=active_intents,
        scanned_prompts=len(prompts),
    )
    summary.update({
        'created_tasks': created,
        'reopened_tasks': reopened,
        'verified_tasks': verified,
        'carried_tasks': carried,
        'resolved_count': len(intents) - len(active_intents),
        'resolution_path': RESOLUTION_PATH,
        'task_id_by_source_key': task_id_by_source_key,
        'queue_path': TASK_QUEUE_PATH,
    })
    return summary


def _build_reconstruction_block(summary: dict[str, Any]) -> str:
    unresolved = summary['intents'][:MAX_VISIBLE_INTENTS]
    lines = [
        BLOCK_START,
        '## Intent Backlog Verification',
        '',
        f"*Strict verification over last {summary['prompt_limit']} operator prompts*",
        '',
    ]

    if summary['unresolved_count'] > 0:
        lines.append(f"**Status:** BLOCKED — {summary['unresolved_count']} unresolved intent(s) remain.")
        lines.append('**Directive:** Keep working. Do not treat the task as complete while this backlog is non-zero.')
    else:
        lines.append('**Status:** CLEAR — no unresolved intent backlog detected.')
        lines.append('**Directive:** Completion is allowed only after this block stays clear on refresh.')

    lines.extend([
        f"**Verification:** scanned={summary['scanned_prompts']} | created={summary['created_tasks']} | reopened={summary['reopened_tasks']} | verified={summary['verified_tasks']} | resolved={summary.get('resolved_count', 0)}",
        '**Rule:** An intent counts as done only when recent file activity clears it or the synced backlog task is verified done.',
        '',
    ])

    if summary.get('resolution_path'):
        lines.append(f"**Resolution Artifact:** `{summary['resolution_path']}`")
        lines.append('')

    if unresolved:
        lines.append('### Unresolved')
        for intent in unresolved:
            task_id = summary['task_id_by_source_key'].get(intent['source_key'], '?')
            refs = intent.get('module_refs') or intent.get('files_open') or []
            ref_text = ', '.join(f'`{ref}`' for ref in refs[:3]) if refs else 'none'
            lines.append(f"- [{intent['status']}] `{task_id}` conf={intent['confidence']:.2f} | {intent['reconstructed'][:96]}")
            lines.append(f"  → refs: {ref_text} | reason: {intent['verification_reason']}")
    else:
        lines.append('### Verification')
        lines.append(f"- last scan cleared all unresolved intents across {summary['scanned_prompts']} operator prompts.")

    lines.extend(['', BLOCK_END])
    return '\n'.join(lines)


def build_reconstruction_block(root: Path, prompt_limit: int = MAX_PROMPTS) -> str:
    return _build_reconstruction_block(synchronize_intent_backlog(root, prompt_limit))


def write_backlog_snapshot(
    root: Path,
    prompt_limit: int = MAX_PROMPTS,
    summary: dict[str, Any] | None = None,
) -> Path:
    root = Path(root)
    if summary is None:
        summary = synchronize_intent_backlog(root, prompt_limit)
    snapshot = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'prompt_limit': summary['prompt_limit'],
        'scanned_prompts': summary['scanned_prompts'],
        'strict_verification': True,
        'unresolved_count': summary['unresolved_count'],
        'abandoned': summary['abandoned'],
        'partial': summary['partial'],
        'cold': summary['cold'],
        'created_tasks': summary['created_tasks'],
        'reopened_tasks': summary['reopened_tasks'],
        'verified_tasks': summary['verified_tasks'],
        'resolved_count': summary.get('resolved_count', 0),
        'resolution_path': summary.get('resolution_path', RESOLUTION_PATH),
        'queue_path': summary['queue_path'],
        'intents': summary['intents'][:MAX_STORED_INTENTS],
    }
    out = root / SNAPSHOT_PATH
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False), encoding='utf-8')
    return out


def inject_into_copilot_instructions(
    root: Path,
    prompt_limit: int = MAX_PROMPTS,
    summary: dict[str, Any] | None = None,
) -> bool:
    root = Path(root)
    cp_path = root / COPILOT_PATH
    if not cp_path.exists():
        return False
    if summary is None:
        summary = synchronize_intent_backlog(root, prompt_limit)

    text = cp_path.read_text(encoding='utf-8')
    block = _build_reconstruction_block(summary)
    pattern = re.compile(r'<!-- pigeon:intent-backlog -->.*?<!-- /pigeon:intent-backlog -->', re.DOTALL)
    if pattern.search(text):
        new_text = pattern.sub(block, text)
    elif '<!-- /pigeon:task-context -->' in text:
        anchor = '<!-- /pigeon:task-context -->'
        idx = text.index(anchor) + len(anchor)
        new_text = text[:idx] + '\n\n' + block + text[idx:]
    else:
        new_text = text.rstrip() + '\n\n' + block + '\n'

    if new_text != text:
        cp_path.write_text(new_text, encoding='utf-8')
    return True


def refresh_intent_backlog(root: Path, prompt_limit: int = MAX_PROMPTS) -> dict[str, Any]:
    summary = synchronize_intent_backlog(root, prompt_limit)
    snapshot = write_backlog_snapshot(root, prompt_limit, summary=summary)
    injected = inject_into_copilot_instructions(root, prompt_limit, summary=summary)
    summary.update({'snapshot_path': str(snapshot), 'injected': injected})
    return summary


if __name__ == '__main__':
    root = Path('.')
    summary = refresh_intent_backlog(root)
    print(f"Scanned {summary['scanned_prompts']} operator prompts")
    print(f"Unresolved backlog: {summary['unresolved_count']}")
    print(f"  - abandoned: {summary['abandoned']}")
    print(f"  - partial: {summary['partial']}")
    print(f"  - cold: {summary['cold']}")
    print(f"Queue sync: created={summary['created_tasks']} reopened={summary['reopened_tasks']} verified={summary['verified_tasks']}")
    print()
    for intent in summary['intents'][:5]:
        print(f"[{intent['status']}] {intent['reconstructed'][:80]}")
