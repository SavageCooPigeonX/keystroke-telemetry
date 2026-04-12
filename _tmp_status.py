"""Quick status check — all modules touched this session."""
from pathlib import Path

# 1. probe system
from src.probe_surface import parse_probe_blocks, harvest_pending_probes, build_resolution_block
from src.probe_resolver import resolve_all_pending
print('probe_surface + probe_resolver: OK')

# 2. query_memory
from src import load_query_memory
result = load_query_memory(Path('.'))
total = result.get('total_queries', 0)
gaps = len(result.get('persistent_gaps', []))
abandons = len(result.get('recent_abandons', []))
print(f'query_memory: OK (queries={total}, gaps={gaps}, abandons={abandons})')

# 3. managed prompt injection wiring
from src.管_cpm_s020.管w_cpm_rmp_s016_v001 import refresh_managed_prompt
print('managed prompt orchestrator: OK')

# 4. self-fix stubs
from src.修f_sf_s013_v012_d0402_初写谱净拆_λVR_βoc import run_self_fix
print('self_fix: OK')

# 5. run tests
print('\n--- running test_all.py ---')
import subprocess, sys
r = subprocess.run([sys.executable, 'test_all.py'], capture_output=True, text=True, encoding='utf-8')
# just show last 5 lines
lines = r.stdout.strip().splitlines()
for ln in lines[-5:]:
    print(ln)
if r.returncode != 0:
    print('STDERR:', r.stderr[-300:] if r.stderr else 'none')
    print(f'EXIT CODE: {r.returncode}')
