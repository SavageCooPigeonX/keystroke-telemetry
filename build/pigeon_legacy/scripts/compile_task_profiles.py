"""Compile last 500 prompts into task profiles via DeepSeek API.

Uses DeepSeek (reasoning model) for codebase-aware clustering — not generic
categories but actual module names, actual incomplete work, actual open loops.

Read layer: each profile = a real recurring task with:
- slug name tied to actual modules (e.g. "tc-overlay-echo-strip", "numeric-surface-pipeline")
- what specifically was attempted and what's still broken
- sample prompts that belong to it
- encoding: intent type, cognitive state, deletion signal

Output: logs/task_profiles.json
"""
from __future__ import annotations
import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

JOURNAL = ROOT / 'logs' / 'prompt_journal.jsonl'
OUT = ROOT / 'logs' / 'task_profiles.json'
ENV = ROOT / '.env'

BATCH_SIZE = 50
MAX_PROMPTS = 500
DEEPSEEK_URL = 'https://api.deepseek.com/v1/chat/completions'


def _load_key() -> str:
    if ENV.exists():
        for line in ENV.read_text('utf-8', errors='ignore').splitlines():
            if line.startswith('DEEPSEEK_API_KEY='):
                return line.split('=', 1)[1].strip()
    return os.environ.get('DEEPSEEK_API_KEY', '')


def _load_prompts(n: int) -> list[dict]:
    lines = [l for l in JOURNAL.read_text('utf-8', errors='ignore').splitlines() if l.strip()]
    out = []
    for line in lines[-n:]:
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


def _deepseek_call(key: str, system: str, user: str, max_tokens: int = 4096) -> str:
    body = json.dumps({
        'model': 'deepseek-chat',
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user},
        ],
        'max_tokens': max_tokens,
        'temperature': 0.1,
    }).encode('utf-8')
    req = urllib.request.Request(
        DEEPSEEK_URL, data=body,
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {key}'},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode('utf-8'))
    return data['choices'][0]['message']['content'].strip()


SYSTEM = """\
You are analyzing prompt history from a keystroke-telemetry codebase.
This is a real Python repo with specific modules: tc_popup_seq001_v001, tc_gemini_seq001_v001, tc_context_seq001_v001_agent_seq001_v001,
intent_numeric_seq001_v001, numeric_surface_seq001_v001, push_cycle, self_fix, file_heat_map, os_hook,
vscdb_poller, thought_completer, prompt_journal, tc_intent_manager_seq001_v001, tc_trajectory_seq001_v001,
operator_stats, unsaid_recon, pigeon_compiler, etc.

The operator is a vibe-coder — they never write code, they steer Copilot with prompts.
Their prompts are messy, typo-filled, stream-of-consciousness.

Your job: extract specific, concrete task profiles. NOT generic software categories.
Name actual broken things. Name actual modules. Be surgical.
"""

CLUSTER_PROMPT = """\
Here are N_PROMPTS operator prompts from this codebase session.
Each has: msg, intent, cognitive_state, deleted_words (unsaid thoughts), module_refs.

Extract 4-8 TASK PROFILES. Each is a recurring concrete goal that appears in multiple prompts.

Rules:
- Name must be a specific slug tied to actual code: "tc-overlay-echo-strip" not "ui-fixes"
- theme must name WHAT IS BROKEN or WHAT NEEDS DOING, not a category
- unresolved_core: the SPECIFIC thing still not working (name the function/file/behavior)
- status: "open" = still broken/incomplete, "partial" = started but not verified, "done" = resolved
- prompt_indices: 0-based indices of prompts in this batch that belong to this profile
- key_modules: actual module names from the codebase, not generic names

Output ONLY valid JSON array (no markdown fences, no explanation):
[{"name":"...","theme":"...","status":"open|partial|done","prompt_indices":[...],"key_modules":[...],"unresolved_core":"...","dominant_state":"...","dominant_intent":"..."},...]

PROMPTS:
PROMPTS_JSON"""

MERGE_SYSTEM = """\
You are merging task profile batches from a keystroke-telemetry codebase audit.
Stay specific — keep actual module names, actual broken behaviors. Do not generalize.
"""

MERGE_PROMPT = """\
You have N_BATCHES batches of task profiles from different time windows of the same session.
Merge into 6-12 final profiles.

Rules:
- Merge profiles that describe the same concrete broken thing
- Keep status = most pessimistic (open > partial > done)  
- Combine key_modules, sum prompt_counts
- unresolved_core: merge the specific failure descriptions, keep the most concrete one
- Add sample_prompts: 2-3 actual verbatim prompt snippets that best represent the profile

Output ONLY valid JSON array (no markdown, no explanation):
[{"name":"...","theme":"...","status":"...","prompt_count":N,"key_modules":[...],"unresolved_core":"...","dominant_state":"...","dominant_intent":"...","sample_prompts":["...","..."]},...]

BATCHES:
BATCHES_JSON"""


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith('```'):
        text = '\n'.join(text.split('\n')[1:])
    if text.endswith('```'):
        text = '\n'.join(text.split('\n')[:-1])
    return text.strip()


def _format_batch(prompts: list[dict]) -> str:
    items = []
    for i, p in enumerate(prompts):
        items.append({
            'i': i,
            'msg': p.get('msg', '')[:250],
            'intent': p.get('intent', ''),
            'state': p.get('cognitive_state', ''),
            'deleted': [w['word'] if isinstance(w, dict) else str(w)
                        for w in p.get('deleted_words', [])][:6],
            'modules': p.get('module_refs', [])[:5],
        })
    return json.dumps(items, indent=2)


def main():
    key = _load_key()
    if not key:
        print('ERROR: no DEEPSEEK_API_KEY found in .env')
        sys.exit(1)

    prompts = _load_prompts(MAX_PROMPTS)
    print(f'Loaded {len(prompts)} prompts → DeepSeek')

    batches = [prompts[i:i+BATCH_SIZE] for i in range(0, len(prompts), BATCH_SIZE)]
    print(f'{len(batches)} batches of ~{BATCH_SIZE}...')

    batch_results = []
    for idx, batch in enumerate(batches):
        print(f'  batch {idx+1}/{len(batches)} ({len(batch)} prompts)...', end=' ', flush=True)
        user = (CLUSTER_PROMPT
                .replace('N_PROMPTS', str(len(batch)))
                .replace('PROMPTS_JSON', _format_batch(batch)))
        try:
            raw = _deepseek_call(key, SYSTEM, user)
            raw = _strip_fences(raw)
            profiles = json.loads(raw)
            if not isinstance(profiles, list):
                profiles = profiles.get('profiles', [])
            # attach sample prompts
            for p in profiles:
                indices = p.get('prompt_indices', [])
                p['sample_prompts'] = [
                    batch[i]['msg'][:120] for i in indices if i < len(batch)
                ][:3]
            batch_results.append({'batch': idx, 'profiles': profiles})
            print(f'got {len(profiles)} profiles')
        except Exception as e:
            print(f'ERROR: {e}')
            batch_results.append({'batch': idx, 'profiles': [], 'error': str(e)})
        time.sleep(0.5)  # rate limit courtesy

    print('Merging...')
    merge_user = (MERGE_PROMPT
                  .replace('N_BATCHES', str(len(batch_results)))
                  .replace('BATCHES_JSON', json.dumps(batch_results, indent=2)[:14000]))
    try:
        raw = _deepseek_call(key, MERGE_SYSTEM, merge_user, max_tokens=6000)
        raw = _strip_fences(raw)
        final_profiles = json.loads(raw)
        if not isinstance(final_profiles, list):
            final_profiles = final_profiles.get('profiles', [])
    except Exception as e:
        print(f'Merge ERROR: {e} — flattening batches instead')
        final_profiles = [p for b in batch_results for p in b.get('profiles', [])]

    out = {
        'generated': datetime.now(timezone.utc).isoformat(),
        'model': 'deepseek-chat',
        'prompt_count': len(prompts),
        'profiles': final_profiles,
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'\nDone. {len(final_profiles)} profiles → {OUT}')

    print('\n── TASK PROFILES ──')
    for p in final_profiles:
        status = p.get('status', '?')
        icon = {'open': 'OPEN', 'partial': 'PARTIAL', 'done': 'DONE'}.get(status, status.upper())
        print(f'\n[{icon}] {p.get("name", "?")}')
        print(f'  {p.get("theme", "")}')
        mods = ', '.join(p.get('key_modules', [])[:6])
        if mods:
            print(f'  modules: {mods}')
        unres = p.get('unresolved_core', '')
        if unres and status != 'done':
            print(f'  unresolved: {unres[:150]}')
        for s in p.get('sample_prompts', [])[:2]:
            print(f'  · {s[:90]}')


if __name__ == '__main__':
    main()
