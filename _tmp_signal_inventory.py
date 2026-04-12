"""Signal source inventory — what exists, what's connected."""
import json
from pathlib import Path

root = Path('.')

# ai_responses.jsonl
resp_path = root / 'logs' / 'ai_responses.jsonl'
if resp_path.exists():
    lines = resp_path.read_text('utf-8', errors='replace').splitlines()
    print(f'ai_responses.jsonl: {len(lines)} entries')
    if lines:
        first = json.loads(lines[0])
        last = json.loads(lines[-1])
        print(f'  first ts: {str(first.get("ts","?"))[:19]}')
        print(f'  last ts:  {str(last.get("ts","?"))[:19]}')
        print(f'  keys: {list(first.keys())}')
else:
    print('ai_responses.jsonl: NOT FOUND')

# prompt_journal
pj_path = root / 'logs' / 'prompt_journal.jsonl'
if pj_path.exists():
    lines = pj_path.read_text('utf-8', errors='replace').splitlines()
    print(f'prompt_journal.jsonl: {len(lines)} entries')
else:
    print('prompt_journal.jsonl: NOT FOUND')

# chat_compositions
cc_path = root / 'logs' / 'chat_compositions.jsonl'
if cc_path.exists():
    lines = cc_path.read_text('utf-8', errors='replace').splitlines()
    print(f'chat_compositions.jsonl: {len(lines)} entries')
else:
    print('chat_compositions.jsonl: NOT FOUND')

# prompt_telemetry
pt_path = root / 'logs' / 'prompt_telemetry_latest.json'
if pt_path.exists():
    pt = json.loads(pt_path.read_text('utf-8'))
    rs = pt.get('running_summary', {})
    print(f'prompt_telemetry: session_n={pt.get("latest_prompt",{}).get("session_n","?")} total={rs.get("total_prompts","?")}')
else:
    print('prompt_telemetry: NOT FOUND')

# reactor state
rs_path = root / 'logs' / 'cognitive_reactor_state.json'
if rs_path.exists():
    rs = json.loads(rs_path.read_text('utf-8'))
    print(f'reactor: fires={rs.get("total_fires",0)} patches={rs.get("patches_applied",0)} streaks={len(rs.get("file_streaks",{}))}')
else:
    print('reactor: NOT FOUND')

# edit_pairs
ep_path = root / 'logs' / 'edit_pairs.jsonl'
if ep_path.exists():
    lines = ep_path.read_text('utf-8', errors='replace').splitlines()
    print(f'edit_pairs.jsonl: {len(lines)} entries')
else:
    print('edit_pairs.jsonl: NOT FOUND')

# learning loop state
ll_path = root / 'learning_loop_state.json'
if ll_path.exists():
    ll = json.loads(ll_path.read_text('utf-8'))
    print(f'learning_loop: cycles={ll.get("total_cycles",0)} unprocessed={ll.get("unprocessed_count",0)}')
else:
    print('learning_loop: NOT FOUND')

# patch applications
pa_path = root / 'logs' / 'patch_applications.jsonl'
if pa_path.exists():
    lines = pa_path.read_text('utf-8', errors='replace').splitlines()
    applied = sum(1 for l in lines if '"applied": true' in l)
    rejected = sum(1 for l in lines if '"applied": false' in l)
    print(f'patch_applications: {len(lines)} total ({applied} applied, {rejected} rejected)')
else:
    print('patch_applications: NOT FOUND')

# reactor audit
ra_path = root / 'logs' / 'reactor_audit.jsonl'
if ra_path.exists():
    lines = ra_path.read_text('utf-8', errors='replace').splitlines()
    print(f'reactor_audit: {len(lines)} entries')
else:
    print('reactor_audit: NOT FOUND (just created, needs first fire)')

# shard training pairs
tp_path = root / 'logs' / 'shards' / 'training_pairs.md'
if tp_path.exists():
    lines = tp_path.read_text('utf-8', errors='replace').splitlines()
    print(f'training_pairs: {len(lines)} lines')
else:
    print('training_pairs: NOT FOUND')

# execution deaths
ed_path = root / 'execution_death_log.json'
if ed_path.exists():
    ed = json.loads(ed_path.read_text('utf-8'))
    entries = ed if isinstance(ed, list) else ed.get('deaths', [])
    print(f'execution_death_log: {len(entries)} deaths')
else:
    print('execution_death_log: NOT FOUND')
