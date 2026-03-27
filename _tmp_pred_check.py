import json
d = json.load(open('pigeon_brain/prediction_calibration.json', encoding='utf-8'))
print(f"Total calibration entries: {d['total']}")
print(f"Overconfidence rate: {d['overconfidence_rate']}")
for b, v in sorted(d['buckets'].items()):
    avg_actual = v['sum_actual']/v['count'] if v['count'] else 0
    avg_conf = v['sum_conf']/v['count'] if v['count'] else 0
    print(f"  confidence={b}: n={v['count']} avg_actual={avg_actual:.3f} avg_conf={avg_conf:.3f} gap={avg_conf-avg_actual:+.3f}")

# Check node memory growth
nm = json.load(open('pigeon_brain/node_memory.json', encoding='utf-8'))
total_entries = sum(len(v.get('entries', [])) for v in nm.values())
total_nodes = len(nm)
print(f"\nNode memory: {total_nodes} nodes, {total_entries} total learning entries")
policies = {k: v.get('policy', {}) for k, v in nm.items() if v.get('policy')}
top = sorted(policies.items(), key=lambda x: x[1].get('score', 0))
print(f"Worst 5 nodes:")
for k, p in top[:5]:
    print(f"  {k}: score={p.get('score',0):.3f} entries={len(nm[k].get('entries',[]))}")
print(f"Best 5 nodes:")
for k, p in top[-5:]:
    print(f"  {k}: score={p.get('score',0):.3f} entries={len(nm[k].get('entries',[]))}")
