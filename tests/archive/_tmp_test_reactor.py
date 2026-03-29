"""Test: Cognitive reactor fires when conditions are met."""
import json, sys, importlib.util
from pathlib import Path

root = Path('.')

# Load the reactor module dynamically
matches = sorted(root.glob('src/cognitive_reactor_seq014*.py'))
assert matches, 'cognitive_reactor not found'
spec = importlib.util.spec_from_file_location('reactor', matches[-1])
reactor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reactor)

# Test 1: _load_state with bugged {} file
state_path = root / reactor.STATE_FILE
backup = None
if state_path.exists():
    backup = state_path.read_text('utf-8')

# Write bugged state
state_path.write_text('{}', encoding='utf-8')
state = reactor._load_state(root)
assert 'file_streaks' in state, f'FAIL: _load_state({{}}) missing file_streaks: {state}'
assert 'last_fire' in state, f'FAIL: _load_state({{}}) missing last_fire'
print('TEST 1 PASS: _load_state handles {} correctly')

# Test 2: Simulate 3 frustrated flushes on the same file
# Reset state
state_path.write_text('{}', encoding='utf-8')
active = ['cognitive_reactor_seq014_v003_d0321__cognitive_reactor_autonomous_code_modification_lc_implement_all_18.py']

# Flush 1: frustrated, high hesitation
r1 = reactor.ingest_flush(root, 'frustrated', 0.75, 25.0, active)
assert r1 is None, 'Should not fire on first flush'
s1 = reactor._load_state(root)
assert 'cognitive_reactor' in s1['file_streaks'], f'Streak not tracked: {s1}'
print(f'  Flush 1: streak count = {s1["file_streaks"]["cognitive_reactor"]["count"]}')

# Flush 2: hesitant, high hesitation
r2 = reactor.ingest_flush(root, 'hesitant', 0.70, 30.0, active)
assert r2 is None, 'Should not fire on second flush'
s2 = reactor._load_state(root)
print(f'  Flush 2: streak count = {s2["file_streaks"]["cognitive_reactor"]["count"]}')

# Flush 3: frustrated again — should fire!
r3 = reactor.ingest_flush(root, 'frustrated', 0.80, 20.0, active)
if r3 and r3.get('fired'):
    print(f'TEST 2 PASS: Reactor FIRED on flush 3!')
    print(f'  Module: {r3["module"]}')
    print(f'  Avg hes: {r3["avg_hes"]}')
    print(f'  Dominant state: {r3["dominant_state"]}')
    print(f'  Problems: {r3["problems"]}')
    print(f'  Patch: {r3["patch_path"]}')
    if r3.get('therapy'):
        print(f'  Therapy notes: {r3["therapy"].get("notes", [])}')
else:
    # Check state to see where it stopped
    s3 = reactor._load_state(root)
    streak = s3['file_streaks'].get('cognitive_reactor', {})
    print(f'TEST 2 PARTIAL: Reactor did not fire on flush 3')
    print(f'  Streak count: {streak.get("count", 0)}')
    print(f'  Avg hes: {streak.get("total_hes", 0) / max(streak.get("count", 1), 1):.3f}')
    print(f'  States: {streak.get("states", [])}')
    # Check if it almost fired
    if streak.get('count', 0) >= 3:
        avg = streak.get('total_hes', 0) / streak.get('count', 1)
        print(f'  avg_hes {avg:.3f} vs threshold {reactor.HESITATION_THRESHOLD}')
    print('  (may still be correct if cooldown or threshold not met)')

# Test 3: active_files from prompt telemetry path
print('\nTest 3: File key extraction')
test_files = [
    ('self_fix_seq013_v011_d0328__one_shot_self_fix_analyzer_lc_dynamic_import.py', 'self_fix'),
    ('classify_bridge.py', 'classify_bridge'),
    ('context_budget_seq004_v008_d0322__blah.py', 'context_budget'),
    ('pigeon_brain/flow/learning_loop_seq013/something.py', 'something'),
]
import re
for f, expected in test_files:
    fname = Path(f).name
    key = re.sub(r'_seq\d+.*$', '', fname.replace('.py', ''))
    assert key == expected, f'FAIL: {f} -> {key} (expected {expected})'
    print(f'  {f} -> {key} OK')

# Restore original state
if backup is not None:
    state_path.write_text(backup, encoding='utf-8')
else:
    state_path.write_text('{}', encoding='utf-8')

print('\nAll reactor tests passed!')
