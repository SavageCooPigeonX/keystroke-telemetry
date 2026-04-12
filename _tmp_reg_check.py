import json
reg = json.loads(open('pigeon_registry.json','r',encoding='utf-8').read())
files = reg.get('files', [])
keywords = ['drift', 'self_fix', 'context_budget', 'push_narra', 'streaming', 'prediction_scorer', 'import_rewriter']
for f in files:
    name = f.get('name', '')
    desc = f.get('desc', '')
    for k in keywords:
        if k in name or k in desc:
            print(f'  name={name[:60]}')
            print(f'  desc={desc[:80]}')
            print(f'  keys={list(f.keys())}')
            print()
            break
