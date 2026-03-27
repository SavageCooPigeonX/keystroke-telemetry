import json

m = json.load(open("pigeon_brain/node_memory.json"))
print(f"NODES WITH MEMORY: {len(m)}")
print()

items = sorted(m.items(), key=lambda x: x[1]["policy"]["rolling_score"])
for k, v in items:
    p = v["policy"]
    print(f"  {k}: score={p['rolling_score']:.3f}  entries={len(v['entries'])}  directive={p['behavioral_directive'][:70]}")

print()
# Show total learnings
total = sum(len(v["entries"]) for v in m.values())
print(f"TOTAL LEARNING ENTRIES: {total}")
