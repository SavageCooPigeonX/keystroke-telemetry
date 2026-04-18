import sys
sys.path.insert(0, '.')
from src.tc_context_seq001_v001_seq001_v001_agent_seq001_v001_seq001_v001 import select_context_numeric, _load_registry
reg = _load_registry()
print(f'registry: {len(reg)} modules')
ns = [r for r in reg if 'numeric_surface_seq001_v001' in r.get('name', '').lower()]
print(f'numeric_surface_seq001_v001 in registry: {len(ns)}')
for r in ns[:3]:
    print('  ', r.get('name'))

ctx = {'unsaid_threads': [], 'hot_modules': [], 'recent_prompts': []}
for buf in ['audit bug profiles and numeric encoding',
            'thought completer context select loop',
            'push cycle rename engine']:
    result = select_context_numeric(buf, ctx, max_files=5)
    print(f'\nbuf: {buf!r}')
    print(f'  numeric hits: {len(result)}')
    for r in result:
        print('   ', r.get('name'), 'score=', r.get('score'))
