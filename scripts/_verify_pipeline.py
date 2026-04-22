"""End-to-end verification: sim fires → overwriter applies → regression gate."""
import sys, json, time, os
from pathlib import Path
import io, contextlib

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# ── suppress DRIFT noise during import ──────────────────────────────────────
import importlib.util

def _load_module(glob_pattern: str, name: str):
    hits = sorted(ROOT.glob(glob_pattern))
    if not hits:
        raise FileNotFoundError(f"No file matching {glob_pattern}")
    spec = importlib.util.spec_from_file_location(name, hits[-1])
    mod = importlib.util.module_from_spec(spec)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        spec.loader.exec_module(mod)
    return mod

print("loading file_sim (suppressing import side-effects)...", flush=True)
fs = _load_module('src/file_sim_seq001_v005_d0421*.py', 'file_sim')

# ── which provider is selected? ──────────────────────────────────────────────
key, provider = fs._load_api_key()
print(f"grader: {provider} ({'key found' if key else 'NO KEY'})", flush=True)

# ── run sim ──────────────────────────────────────────────────────────────────
PROMPT = "confirm sim fires self fix runs files talk meta comments deepseek auto fix"
print(f"\nrunning sim (top_n=3)...\n  prompt: {PROMPT[:60]}", flush=True)
t0 = time.perf_counter()
results = fs.run_sim(PROMPT, top_n=3)
elapsed = time.perf_counter() - t0
print(f"\ndone in {elapsed:.1f}s — {len(results)} results", flush=True)

for r in results:
    nc = "NEEDS_CHANGE" if r["needs_change"] else "no-change"
    print(f"  [{nc}] conf={r['confidence']:.2f} {r['file_stem'][:50]}")
    print(f"    {r['reason'][:80]}")

# ── wait for background overwriter threads ───────────────────────────────────
any_triggered = any(r["needs_change"] and r["confidence"] >= 0.85 for r in results)
if any_triggered:
    print("\noverwriter threads triggered — waiting 40s...", flush=True)
    time.sleep(40)
else:
    print("\nno overwrites triggered (conf < 0.85 or needs_change=False)", flush=True)

# ── check logs ───────────────────────────────────────────────────────────────
ol = ROOT / "logs" / "file_overwrites.jsonl"
sl = ROOT / "logs" / "sim_results.jsonl"

if ol.exists():
    entries = [json.loads(l) for l in ol.read_text("utf-8").strip().splitlines() if l]
    print(f"\nfile_overwrites.jsonl: {len(entries)} total entries")
    for e in entries[-5:]:
        reg = e.get("regression_passed")
        print(f"  {'✓' if e['applied'] else '✗'} {e['stem'][:40]} applied={e['applied']} reg={reg}")
        if e.get("diff"):
            print(f"    diff: {e['diff'][:60]}")
else:
    print("\nfile_overwrites.jsonl: not found")

# ── show file cortex for a graded file ───────────────────────────────────────
if results:
    stem = results[0]["file_stem"]
    profiles = fs._load_profiles(ROOT)
    cortex = fs._cortex_summary(profiles.get(stem, {}))
    print(f"\nfile cortex [{stem[:35]}]:")
    print(f"  {cortex[:200]}")
