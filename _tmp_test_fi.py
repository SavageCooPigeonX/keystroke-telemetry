import json, re, os
from pathlib import Path

root = Path(".")
has_key = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"))
print("GEMINI_API_KEY set:", has_key)

reg = json.loads((root / "pigeon_registry.json").read_text("utf-8"))
entries = reg.get("files", reg) if isinstance(reg, dict) else reg

BETA_RE = re.compile(r"_β(\w+?)(?:_|\.py$|$)")
BUG_SEV = {"oc": 0.8, "hi": 0.7, "hc": 0.6, "de": 0.4, "dd": 0.3, "qn": 0.2}

def prio(e):
    bugs = [c for m in BETA_RE.findall(e.get("path", "")) for c in re.findall(r"[a-z]{2}", m)]
    return sum(BUG_SEV.get(b, 0) for b in bugs), bugs

top = sorted(entries, key=lambda e: prio(e)[0], reverse=True)[:10]
print(f"\nTop 10 by bug priority (out of {len(entries)} files):")
for e in top:
    score, bugs = prio(e)
    path = e.get("path", "")[:60]
    print(f"  {e['name'][:40]:<40} bugs={bugs} score={score:.1f}")
    print(f"    {path}")

# Check import works
try:
    from pigeon_brain.flow.读f_fi_s016_v001_d0410_λFT import (
        run_interrogation_sweep, print_agent_briefing, get_file_understanding
    )
    print("\n✓ file_interrogator imported OK")
    # Check existing understanding
    nm_path = root / "pigeon_brain/node_memory.json"
    nm = json.loads(nm_path.read_text("utf-8")) if nm_path.exists() else {}
    with_understanding = [k for k, v in nm.items() if v.get("file_understanding")]
    print(f"  Nodes already with file_understanding: {len(with_understanding)}")
    for n in with_understanding[:3]:
        u = nm[n]["file_understanding"]
        print(f"    {n}: {u.get('autonomous_directive','?')[:60]}")
except Exception as exc:
    print(f"\n✗ Import failed: {exc}")
