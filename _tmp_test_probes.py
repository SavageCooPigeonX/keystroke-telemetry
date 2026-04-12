"""Test probe_surface + probe_resolver end-to-end."""
from pathlib import Path
from src.probe_surface import parse_probe_blocks, harvest_pending_probes, build_resolution_block, write_resolution
from src.probe_resolver import resolve_all_pending, resolve_probe

# 1. test parse
sample = '''here is my response

<!-- probe:ask
module: flow_engine
question: does get_surface_tensor return flat dict or nested?
candidates: flat_dict | nested_object
confidence: 0.45
context: editing predictor.py line 88
-->

some more text

<!-- probe:ask
module: cognitive_reactor
question: should streak decay be linear or exponential?
candidates: linear | exponential
confidence: 0.30
-->
'''

probes = parse_probe_blocks(sample)
print(f'Parsed {len(probes)} probes:')
for p in probes:
    print(f'  [{p["module"]}] {p["question"]} (conf={p["confidence"]}, candidates={p["candidates"]})')

assert len(probes) == 2, f'Expected 2 probes, got {len(probes)}'
assert probes[0]['module'] == 'flow_engine'
assert probes[0]['candidates'] == ['flat_dict', 'nested_object']
assert probes[1]['confidence'] == 0.30
print('  PASS: parse')

# 2. test build block with no data
block = build_resolution_block(Path('.'))
print(f'\nResolution block preview:')
print(block[:300])
assert 'Probe Resolutions' in block
print('  PASS: build_resolution_block')

# 3. test resolver on empty
result = resolve_all_pending(Path('.'), auto_write=False)
print(f'\nResolver: {result["total_pending"]} pending, {result["resolved"]} resolved, {result["unresolved"]} unresolved')
print('  PASS: resolve_all_pending')

# 4. test write_resolution round-trip
import tempfile, json, os
with tempfile.TemporaryDirectory() as td:
    root = Path(td)
    (root / 'logs').mkdir()
    fake_probe = {'module': 'test_mod', 'question': 'is X flat or nested?', 'candidates': ['flat', 'nested']}
    fake_resolution = {'answer': 'flat dict per contract', 'source': 'prompt_journal', 'confidence': 0.85}
    write_resolution(root, fake_probe, fake_resolution)
    out = root / 'logs' / 'probe_resolutions.jsonl'
    assert out.exists()
    entry = json.loads(out.read_text(encoding='utf-8').strip())
    assert entry['module'] == 'test_mod'
    assert entry['resolution'] == 'flat dict per contract'
    print(f'\n  Written resolution: module={entry["module"]} answer={entry["resolution"]}')
    print('  PASS: write_resolution')

# 5. test block generation with data
    block = build_resolution_block(root)
    assert 'test_mod' in block
    assert 'flat dict per contract' in block
    print(f'\n  Block with data ({len(block)} chars):')
    print(block)
    print('  PASS: build_resolution_block with data')

print('\n=== ALL PROBE TESTS PASSED ===')
