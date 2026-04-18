"""Quick test for push_baseline_seq001_v001 pipeline."""
from src.push_baseline_seq001_v001_seq001_v001 import assess_on_push, build_drift_report
from pathlib import Path

root = Path('.')
result = assess_on_push(root, ['src/push_baseline_seq001_v001.py', 'src/interlinker_seq001_v001.py'])
print('assessed:', result['modules_assessed'])
print('drift:', result['total_drift']) 
print('voids:', result['total_voids'])
for k, v in result['results'].items():
    print(f"  {k}: state={v['state']} voids={v['voids']}")

report = build_drift_report(root)
print()
print(report[:600])
