"""Temp: seed escalation and check state."""
import sys, json
sys.path.insert(0, '.')
from pathlib import Path

root = Path('.')
reg = json.loads((root / 'pigeon_registry.json').read_text('utf-8'))

from src.escalation_engine import check_and_escalate
result = check_and_escalate(root, registry=reg)

st = json.loads((root / 'logs/escalation_state.json').read_text('utf-8'))
mods = st.get('modules', {})

by_level = {}
for n, m in mods.items():
    lv = m.get('level', 0)
    by_level.setdefault(lv, []).append(n)

NAMES = ['REPORT', 'ASK', 'INSIST', 'WARN', 'ACT', 'VERIFY']
print(f'Modules seeded: {len(mods)}')
for lv in sorted(by_level):
    print(f'\n  Level {lv} ({NAMES[lv]}): {len(by_level[lv])} modules')
    for n in by_level[lv][:5]:
        m = mods[n]
        conf = m.get('confidence', 0)
        passes = m.get('passes_ignored', 0)
        bug = m.get('bug_type', '?')
        print(f'    {n}: conf={conf:.2f} passes={passes} bug={bug}')
    if len(by_level[lv]) > 5:
        print(f'    ...+{len(by_level[lv]) - 5} more')

# Show modules closest to ACT (high conf + high passes)
print('\n--- CLOSEST TO AUTONOMOUS ACTION ---')
ranked = [(n, m.get('confidence', 0), m.get('passes_ignored', 0), m.get('bug_type', '?'))
          for n, m in mods.items()]
ranked.sort(key=lambda x: (x[1], x[2]), reverse=True)
for n, conf, passes, bug in ranked[:10]:
    gates = []
    gates.append('FIX' if bug in {'over_hard_cap', 'hardcoded_import', 'dead_export', 'duplicate_docstring'} else 'no_fix')
    gates.append(f'conf={conf:.2f}' + (' OK' if conf >= 0.75 else ' LOW'))
    gates.append(f'passes={passes}' + (' OK' if passes >= 10 else ' LOW'))
    print(f'  {n}: {" | ".join(gates)}')
