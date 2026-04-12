"""Test the file semantic layer."""
from pathlib import Path
from src.file_semantic_layer import inspect_module, grow_on_push, build_semantic_report

root = Path('.')

# test inspection
for stem in ['interlinker', 'push_baseline', 'escalation_engine']:
    print(inspect_module(root, stem))
    print()

# test push growth
result = grow_on_push(root, ['src/push_baseline.py', 'src/interlinker.py'])
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
