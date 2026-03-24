import json
data = json.loads(open('pigeon_brain/context_veins.json','r',encoding='utf-8').read())
ns = data['node_scores']
ranked = sorted(ns.items(), key=lambda x: -x[1]['clot_score'])[:20]
for name, s in ranked:
    print(f"  {name:40s} clot={s['clot_score']:.3f} vein={s['vein_score']:.3f} in={s['in_degree']} out={s['out_degree']} sigs={s['clot_signals']}")
print()
print("Isolated nodes (0 in, 0 out):")
for name, s in ns.items():
    if s['in_degree'] == 0 and s['out_degree'] == 0:
        print(f"  {name}")
print()
print("Orphans (0 in, >0 out):")
for name, s in ns.items():
    if s['in_degree'] == 0 and s['out_degree'] > 0:
        print(f"  {name:40s} out={s['out_degree']} sigs={s['clot_signals']}")
