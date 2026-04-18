"""Quick check: what data has accumulated since launch?"""
import json, pathlib

root = pathlib.Path(".")

# Grades
gl = (root / "logs/completion_grades.jsonl").read_text(encoding="utf-8").strip().splitlines()
live = len(gl) - 246
print(f"=== Grades: {len(gl)} total, {live} live ===")
for line in gl[-5:]:
    g = json.loads(line)
    print(f"  {g.get('outcome','?'):12s}  comp={g.get('composite',0):.2f}  rel={g.get('relevance',0):.2f}")

# Profile sections + intelligence
p = json.loads((root / "logs/operator_profile_tc.json").read_text(encoding="utf-8"))
secs = p.get("shards", {}).get("sections", {})
print(f"\n=== Sections: {list(secs.keys()) if secs else 'EMPTY'} ===")
for name, sec in (secs or {}).items():
    n = sec.get("sample_count", 0)
    if n > 0:
        print(f"  {name}: {n} samples, intent={sec.get('dominant_intent','?')}")

intel = p.get("shards", {}).get("intelligence", {})
print(f"\n=== Intelligence: {intel.get('secret_count', 0)} secrets ===")
for s in intel.get("secrets", []):
    print(f"  [{s.get('type','?')}] {s.get('evidence','')[:80]}")

# Summary
summ = json.loads((root / "logs/completion_grade_summary.json").read_text(encoding="utf-8"))
print(f"\n=== Grade Summary ===")
print(f"  composite={summ.get('avg_composite',0):.3f}  accept={summ.get('accept_rate',0):.1%}  trend={summ.get('trend','?')}")

# Check if update_profile_from_composition is called anywhere
import ast
popup = ast.parse((root / "src/tc_popup_seq001_v001.py").read_text(encoding="utf-8"))
calls = [n.func.attr for n in ast.walk(popup) if isinstance(n, ast.Call) and hasattr(n.func, "attr")]
comp_call = "update_profile_from_composition" in calls
print(f"\n=== Dead Code Check ===")
print(f"  update_profile_from_composition called in popup: {comp_call}")

print(f"\n=== Samples: {p.get('samples', 0)} ===")
