"""Survey data sources for pair dynamics."""
import json
from pathlib import Path

root = Path(".")

print("=== shard learning ===")
shards = root / "logs" / "shards"
if shards.exists():
    for f in sorted(shards.glob("*.md")):
        lines = f.read_text("utf-8").splitlines()
        print(f"  {f.name}: {len(lines)} lines")

print("\n=== mutation scores ===")
ms = root / "logs" / "mutation_scores.json"
if ms.exists():
    d = json.loads(ms.read_text("utf-8"))
    print(f"  total_pairs: {d.get('total_pairs')}")
    print(f"  total_mutations: {d.get('total_mutations')}")

print("\n=== reactor state ===")
rs = root / "logs" / "cognitive_reactor_state.json"
if rs.exists():
    d = json.loads(rs.read_text("utf-8"))
    print(f"  fires: {d.get('total_fires')}")
    print(f"  patches_applied: {d.get('patches_applied')}")
    print(f"  last_fire ts: {d.get('last_fire',{}).get('ts','?')}")

print("\n=== patch applications ===")
pa = root / "logs" / "patch_applications.jsonl"
if pa.exists():
    lines = pa.read_text("utf-8").strip().splitlines()
    print(f"  {len(lines)} entries")
else:
    print("  no patches applied yet")

print("\n=== edit pairs ===")
ep = root / "logs" / "edit_pairs.jsonl"
if ep.exists():
    lines = ep.read_text("utf-8").strip().splitlines()
    print(f"  {len(lines)} prompt-to-file pairings")

print("\n=== rework log ===")
rw = root / "rework_log.json"
if rw.exists():
    d = json.loads(rw.read_text("utf-8"))
    entries = d if isinstance(d, list) else d.get("entries", [])
    verdicts = {}
    for e in entries:
        v = e.get("verdict", "?")
        verdicts[v] = verdicts.get(v, 0) + 1
    print(f"  {len(entries)} entries, verdicts: {verdicts}")

print("\n=== prompt journal ===")
pj = root / "logs" / "prompt_journal.jsonl"
if pj.exists():
    lines = pj.read_text("utf-8").strip().splitlines()
    print(f"  {len(lines)} prompts logged")

print("\n=== copilot prompt mutations ===")
pm = root / "logs" / "copilot_prompt_mutations.json"
if pm.exists():
    d = json.loads(pm.read_text("utf-8"))
    print(f"  {d.get('total_mutations', '?')} mutations tracked")
