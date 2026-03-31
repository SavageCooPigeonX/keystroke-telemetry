from pathlib import Path
import importlib.util

# Manually refresh task-context
matches = sorted(Path('.').glob('src/dynamic_prompt_seq017*.py'))
spec = importlib.util.spec_from_file_location('dyn', matches[-1])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.inject_task_context(Path('.'))
print('task-context refreshed')

# Now run staleness check
matches2 = sorted(Path('.').glob('src/staleness_alert_seq030*.py'))
spec2 = importlib.util.spec_from_file_location('sa', matches2[-1])
mod2 = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(mod2)
stale = mod2.check_staleness(Path('.'))
if stale:
    print(f'Still stale: {len(stale)} blocks')
    for s in stale:
        print(f'  {s["block"]}: {s["reason"]}')
else:
    print('ALL BLOCKS FRESH')

mod2.inject_staleness_alert(Path('.'))

t = open('.github/copilot-instructions.md', 'r', encoding='utf-8').read()
has_alert = '<!-- pigeon:staleness-alert -->' in t
print(f'Alert block present: {has_alert}')
