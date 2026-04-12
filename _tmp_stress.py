"""Stress test: dynamic task injection."""
import sys, json, time
sys.path.insert(0,'.')
from pathlib import Path
root = Path('.')

# 1. Check current state
mem = json.loads((root/'pigeon_brain/node_memory.json').read_text())
print(f'=== STRESS TEST START ===')
print(f'Nodes before: {len(mem)}')
nodes_with_policy = len([n for n in mem.values() if 'policy' in n])
print(f'Nodes with policy: {nodes_with_policy}')

# 2. Inject a dynamic task and run learning
from pigeon_brain.flow.node_memory_seq008 import append_learning

# Simulate 5 dynamic task injections
for i in range(5):
    task = f'dynamic_stress_task_{i}'
    result = append_learning(
        root,
        node=f'stress_test_node_{i}',
        electron_id=f'stress_{i}_{int(time.time())}',
        task_seed=task,
        contribution_summary=f'stress test contribution {i}',
        credit_score=0.7 + (i * 0.05),
        outcome_loss=0.1 - (i * 0.02),
    )
    has_policy = 'policy' in result
    print(f'  Injected: stress_test_node_{i} -> policy={has_policy}')

# 3. Verify persistence
mem2 = json.loads((root/'pigeon_brain/node_memory.json').read_text())
print(f'Nodes after: {len(mem2)}')
new_nodes = len(mem2) - len(mem)
print(f'New nodes: {new_nodes}')
print('=== STRESS TEST PASS ===' if new_nodes >= 5 else '=== STRESS TEST FAIL ===')
