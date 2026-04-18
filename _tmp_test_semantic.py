"""Test the file semantic layer."""
from pathlib import Path
from src.file_semantic_layer_seq001_v001_seq001_v001 import inspect_module, grow_on_push, build_semantic_report

root = Path('.')

# test inspection
for stem in ['interlinker_seq001_v001', 'push_baseline_seq001_v001', 'escalation_engine_seq001_v001']:
    print(inspect_module(root, stem))
    print()

# test push growth
result = grow_on_push(root, ['src/push_baseline_seq001_v001.py', 'src/interlinker_seq001_v001.py'])
print(f"\n=== GROWTH RESULT ===")
print(f"processed: {result['modules_processed']}")
print(f"escalated: {result['escalated']}")
print(f"growing: {result['growing']}")
for a in result['actions']:
    print(f"  {a['module']}: {a['action']} — {a.get('reason', '')}")

# test report
report = build_semantic_report(root)
print(f"\n=== REPORT ===")
print(report[:600])
