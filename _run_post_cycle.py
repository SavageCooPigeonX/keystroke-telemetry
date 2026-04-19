"""_run_post_cycle.py — Manually trigger self_fix + push_narrative for latest commit."""
import importlib.util, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Load .env
env_path = Path('.env')
if env_path.exists():
    for line in env_path.read_text('utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, _, v = line.partition('=')
        k = k.strip(); v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v

print(f'DEEPSEEK: {"ok" if os.environ.get("DEEPSEEK_API_KEY") else "MISSING"}')

def load_glob(folder, pattern):
    root = Path('.')
    matches = sorted((root / folder).glob(f'{pattern}.py'))
    if not matches: return None
    spec = importlib.util.spec_from_file_location(matches[-1].stem, matches[-1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

import subprocess
h = subprocess.run(['git', 'log', '-1', '--format=%h'], capture_output=True, text=True).stdout.strip()
msg = subprocess.run(['git', 'log', '-1', '--format=%s'], capture_output=True, text=True).stdout.strip()
changed = subprocess.run(
    ['git', 'diff', '--name-only', 'HEAD~2', 'HEAD'],
    capture_output=True, text=True, encoding='utf-8'
).stdout.strip().splitlines()
changed_py = [f for f in changed if f.endswith('.py')]
print(f'Commit: {h} — {msg}')
print(f'Changed py files: {len(changed_py)}')

from pigeon_compiler.rename_engine import load_registry
registry = load_registry(Path('.'))

# Self-fix
sf_mod = load_glob('src', '修f_sf_s013*')
if sf_mod:
    print('\n[self_fix] running...')
    try:
        r = sf_mod.run_self_fix(Path('.'), registry)
        print(f'  bugs found: {r.get("total_bugs", 0)} | over_cap: {r.get("over_cap", 0)}')
        if hasattr(sf_mod, 'write_self_fix_report'):
            path = sf_mod.write_self_fix_report(Path('.'), r, h)
            print(f'  report → {path}')
    except Exception as e:
        import traceback; traceback.print_exc()
else:
    print('[self_fix] module not found')

# Push narrative
narr_mod = load_glob('src', '叙p_pn_s012*')
if narr_mod:
    print('\n[push_narrative] generating...')
    try:
        from pigeon_compiler.rename_engine import load_registry
        registry = load_registry(Path('.'))
        # Get intent from commit message
        words = msg.replace('feat:', '').replace('fix:', '').strip().split()[:3]
        intent = '_'.join(w.lower() for w in words)
        result = narr_mod.generate_push_narrative(
            Path('.'), intent, h, changed_py, registry)
        print(f'  narrative → {result}')
    except Exception as e:
        import traceback; traceback.print_exc()
else:
    print('[push_narrative] module not found')

print('\nDone.')
