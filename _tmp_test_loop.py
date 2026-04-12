"""Temporary stress test for learning loop."""
import sys, json, traceback
sys.path.insert(0, '.')
from pathlib import Path

root = Path('.')

# Check journal
journal_path = root / 'logs/prompt_journal.jsonl'
entries = [json.loads(l) for l in journal_path.read_text(encoding='utf-8').strip().split('\n') if l.strip()]
print(f'Journal: {len(entries)} entries')

# Check flow log
flow_log = root / 'pigeon_brain/flow/flow_log.jsonl'
if flow_log.exists():
    fwd = [json.loads(l) for l in flow_log.read_text(encoding='utf-8').strip().split('\n') if l.strip()]
    print(f'Flow log: {len(fwd)} forward passes')
else:
    print('Flow log: NOT FOUND')

# Check loop state
loop_state = root / 'pigeon_brain/flow/loop_state.json'
if loop_state.exists():
    st = json.loads(loop_state.read_text(encoding='utf-8'))
    print(f'Loop state: cycle={st.get("cycle")}, fwd={st.get("total_forward")}, bwd={st.get("total_backward")}')

# Run single cycle with detailed error logging
from pigeon_brain.flow.learning_loop_seq013 import run_single_cycle
state = {'cycle': 0, 'last_journal_idx': 0, 'total_forward': 0, 'total_backward': 0}
if entries:
    e = entries[-1]
    print(f'Testing entry: {e.get("msg", "")[:50]}...')
    try:
        res = run_single_cycle(root, e, state, use_deepseek=False)
        print(f'Result: skipped={res.get("skipped")}, reason={res.get("reason", "none")}')
        print(f'Counters: fwd={state["total_forward"]}, bwd={state["total_backward"]}')
    except Exception as ex:
        print(f'SINGLE CYCLE FAILED: {ex}')
        traceback.print_exc()

# Check node memory with detailed error  
try:
    from pigeon_brain.flow.node_memory_seq008 import load_memory
    mem = load_memory(root)
    nodes_with_data = [n for n, v in mem.get('nodes', {}).items() if v.get('raw')]
    print(f'Node memory: {len(mem.get("nodes", {}))} nodes, {len(nodes_with_data)} with learning data')
except Exception as ex:
    print(f'Node memory load FAILED: {ex}')
    traceback.print_exc()
