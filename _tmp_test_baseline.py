"""Quick test for push_baseline pipeline."""
from src.push_baseline import assess_on_push, build_drift_report
from pathlib import Path

root = Path('.')
result = assess_on_push(root, ['src/push_baseline.py', 'src/interlinker.py'])
print('assessed:', result['modules_assessed'])
print('drift:', result['total_drift']) 
print('voids:', result['total_voids'])
for k, v in result['results'].items():
    print(f"  {k}: state={v['state']} voids={v['voids']}")

report = build_drift_report(root)
print()
print(report[:600])
