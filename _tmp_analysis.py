import json
from pathlib import Path

root = Path(".")

# Node memory deep analysis
nm = json.loads((root / "pigeon_brain/node_memory.json").read_text(encoding="utf-8"))
nodes_by_entries = []
for name, data in nm.items():
    entries = data.get("entries", []) if isinstance(data, dict) else data
    if entries:
        credits = [e.get("credit_score", 0) for e in entries if isinstance(e, dict)]
        losses = [e.get("outcome_loss", 0) for e in entries if isinstance(e, dict)]
        avg_c = sum(credits) / len(credits) if credits else 0
        avg_l = sum(losses) / len(losses) if losses else 0
        nodes_by_entries.append((name, len(entries), avg_c, avg_l))

nodes_by_entries.sort(key=lambda x: -x[1])
print("=== TOP 15 NODES BY MEMORY DEPTH ===")
for n, ct, ac, al in nodes_by_entries[:15]:
    print(f"  {n:40s} entries={ct:4d} avg_credit={ac:.3f} avg_loss={al:.3f}")

print()
print("=== BEST LEARNERS (highest avg credit) ===")
nodes_by_entries.sort(key=lambda x: -x[2])
for n, ct, ac, al in nodes_by_entries[:10]:
    print(f"  {n:40s} entries={ct:4d} avg_credit={ac:.3f} avg_loss={al:.3f}")

print()
print("=== WORST PERFORMERS (lowest avg credit) ===")
nodes_by_entries.sort(key=lambda x: x[2])
for n, ct, ac, al in nodes_by_entries[:10]:
    print(f"  {n:40s} entries={ct:4d} avg_credit={ac:.3f} avg_loss={al:.3f}")

# Flow log pattern analysis
fl_lines = [json.loads(l) for l in open("pigeon_brain/flow_log.jsonl", "r", encoding="utf-8") if l.strip()]
types = {}
for e in fl_lines:
    t = e.get("type", "unknown")
    types[t] = types.get(t, 0) + 1
print()
print(f"=== FLOW LOG: {len(fl_lines)} entries ===")
for t, c in sorted(types.items(), key=lambda x: -x[1]):
    print(f"  {t}: {c}")

# Recent flow entries
print()
print("=== RECENT FLOW (last 10) ===")
for e in fl_lines[-10:]:
    seed = str(e.get("task_seed", ""))[:60]
    print(f"  {e.get('type', '?'):12s} seed={seed}")

# Prediction scores analysis
ps = json.loads((root / "pigeon_brain/prediction_scores.json").read_text(encoding="utf-8"))
print()
print(f"=== PREDICTION SCORES: {len(ps)} entries ===")
if ps:
    f1_scores = [s.get("f1", 0) for s in ps if isinstance(s, dict)]
    combined = [s.get("combined", 0) for s in ps if isinstance(s, dict)]
    if f1_scores:
        print(f"  Avg F1: {sum(f1_scores)/len(f1_scores):.3f}")
    if combined:
        print(f"  Avg combined: {sum(combined)/len(combined):.3f}")
    # By mode
    modes = {}
    for s in ps:
        if isinstance(s, dict):
            m = s.get("mode", "unknown")
            f = s.get("f1", 0)
            if m not in modes:
                modes[m] = []
            modes[m].append(f)
    for m, scores in modes.items():
        print(f"  Mode '{m}': avg_f1={sum(scores)/len(scores):.3f} count={len(scores)}")
