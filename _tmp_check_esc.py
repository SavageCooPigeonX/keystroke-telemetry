"""Quick check: escalation state + run tests."""
import json, sys, subprocess
from pathlib import Path

root = Path('.').resolve()

# 1. Check escalation state
state = json.loads((root / 'logs' / 'escalation_state.json').read_text('utf-8'))
mods = state.get('modules', {})
print(f"=== ESCALATION STATE: {len(mods)} modules ===")
for m, i in sorted(mods.items(), key=lambda x: -x[1]['confidence']):
    print(f"  {m}: L{i['level']} conf={i['confidence']:.2f} passes={i['passes_ignored']} type={i['bug_type']}")

# 2. Run tests
print("\n=== RUNNING TESTS ===")
r = subprocess.run([sys.executable, 'test_all.py'], capture_output=True, text=True, timeout=60)
print(r.stdout[-500:] if len(r.stdout) > 500 else r.stdout)
if r.returncode != 0:
    print(f"STDERR: {r.stderr[-300:]}")
print(f"Exit code: {r.returncode}")
