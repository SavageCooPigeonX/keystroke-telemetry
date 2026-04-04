"""Quick runner to test numeric surface generation."""
from pathlib import Path
from src.numeric_surface import generate_surface
import json

p = generate_surface(Path("."))
d = json.loads(p.read_text("utf-8"))
s = d["stats"]
print(f"nodes: {s['nodes']} | edges: {s['total_edges']} | clusters: {s['clusters']} | hot: {s['hot_nodes']} | bugged: {s['bugged_nodes']}")
print()

print("Traversal:")
for t in d["traversal"][:8]:
    print(f"  {t}")
print()

# Hot nodes
hot = [(k, v) for k, v in d["nodes"].items() if v.get("heat", 0) > 0.2]
hot.sort(key=lambda x: -x[1]["heat"])
print("Hot nodes:")
for name, v in hot[:12]:
    cl = v.get("cluster", "-")
    pers = v.get("personality", "")
    print(f"  {name:30s} heat={v['heat']} dual={v['dual_score']} cluster={cl} {pers}")
print()

# Bugged nodes
bugged = [(k, v) for k, v in d["nodes"].items() if v.get("bugs")]
print(f"Bugged ({len(bugged)}):")
for name, v in bugged[:12]:
    print(f"  {name:30s} bugs={v['bugs']} tokens={v['tokens']}")

# Clusters
cluster_members = {}
for name, v in d["nodes"].items():
    cl = v.get("cluster")
    if cl:
        cluster_members.setdefault(cl, []).append(name)
print(f"\nClusters ({len(cluster_members)}):")
for cl, members in sorted(cluster_members.items()):
    print(f"  {cl}: {', '.join(members[:6])}")
