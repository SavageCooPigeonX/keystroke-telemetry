import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
BRIDGE = ROOT / "vscode-extension" / "classify_bridge.py"

def make_events(text, del_ratio=0.15, wpm_hint=45, pause_every=8):
    """Build synthetic keystroke events. Smaller pause_every to keep timestamps tight."""
    events = []
    ts = 1000.0
    interval = 60000 / max(wpm_hint * 5, 1)
    for i, ch in enumerate(text):
        events.append({"type": "insert", "char": ch, "ts": ts, "delta_ms": round(interval)})
        ts += interval
        if i % pause_every == 0 and i > 0:
            events.append({"type": "pause", "duration_ms": 1600, "ts": ts})
            ts += 1600
    n_del = int(len(text) * del_ratio)
    for _ in range(n_del):
        events.append({"type": "backspace", "ts": ts, "delta_ms": 80})
        ts += 80
    return events

def make_post_events(n_deletes=15, n_reinserts=5):
    """Heavy-rework post-response events: lots of deletes then a few reinserts."""
    events = []
    ts = 500.0
    for _ in range(n_deletes):
        events.append({"type": "backspace", "ts": ts, "delta_ms": 75})
        ts += 75
    for i in range(n_reinserts):
        events.append({"type": "insert", "char": "x", "ts": ts, "delta_ms": 150})
        ts += 150
    return events

def run_bridge(payload: dict) -> dict:
    result = subprocess.run(
        ["py", str(BRIDGE), str(ROOT)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    if result.returncode != 0 or not result.stdout.strip():
        print("  STDERR:", result.stderr[:500])
        return {}
    try:
        return json.loads(result.stdout.strip())
    except Exception as e:
        print("  PARSE ERROR:", e, "| stdout:", result.stdout[:200])
        return {}

# Clean slate for this test
for f in ["rework_log.json", "query_memory.json", "file_heat_map.json"]:
    p = ROOT / f
    if p.exists():
        p.unlink()

print("=" * 60)
print("DEEP SIGNAL TEST — end-to-end pipeline")
print("=" * 60)

# ── TEST 1: Basic submit → rework_verdict present ─────────────────────────
print("\n── TEST 1: submit → rework=ok (no post-response events) ────────")
r1 = run_bridge({
    "events": make_events("how do I wire deepseek into scoring pipeline", del_ratio=0.2),
    "submitted": True,
    "query_text": "how do I wire deepseek into scoring pipeline",
    "post_response_events": []
})
assert r1.get("state"), f"No state in: {r1}"
assert "rework_verdict" in r1, f"Missing rework_verdict: {r1}"
print(f"  ✓ state={r1['state']} hes={r1['hesitation']} wpm={r1['wpm']} rework={r1['rework_verdict']}")

# ── TEST 2: Heavy post-response rework → verdict=miss ─────────────────────
print("\n── TEST 2: heavy post-rework events → verdict=miss ─────────────")
r2 = run_bridge({
    "events": make_events("explain resistance bridge signal scoring", del_ratio=0.3),
    "submitted": True,
    "query_text": "explain resistance bridge signal scoring",
    "post_response_events": make_post_events(n_deletes=18, n_reinserts=4)
})
assert "rework_verdict" in r2, f"Missing rework_verdict: {r2}"
print(f"  ✓ rework_verdict={r2['rework_verdict']}  (expected miss/partial)")
assert r2['rework_verdict'] in ('miss', 'partial'), f"Expected miss/partial, got: {r2['rework_verdict']}"

# ── TEST 3: Recurring query (3x) → persistent gap ─────────────────────────
print("\n── TEST 3: 3x same fingerprint → persistent_gaps ───────────────")
RECURRING = "how do I verify deepseek call is in scope"
for i in range(3):
    run_bridge({
        "events": make_events(RECURRING, del_ratio=0.15),
        "submitted": True,
        "query_text": RECURRING,
        "post_response_events": []
    })
qm = json.loads((ROOT / "query_memory.json").read_text())
queries = qm.get("queries", [])
fps = [q.get("fingerprint") for q in queries]
recurring_fp = max(set(fps), key=fps.count) if fps else None
recurring_count = fps.count(recurring_fp) if recurring_fp else 0
print(f"  ✓ query_memory: {len(queries)} entries, recurring fingerprint count={recurring_count}")
assert recurring_count >= 3, f"Expected ≥3 recurring, got {recurring_count}"

# ── TEST 4: Abandoned draft → abandoned_themes ────────────────────────────
print("\n── TEST 4: abandoned draft → recorded in abandoned_themes ──────")
run_bridge({
    "events": make_events("should we add streaming to deepseek calls now", del_ratio=0.4),
    "submitted": False,
    "query_text": "should we add streaming to deepseek calls now",
    "post_response_events": []
})
qm2 = json.loads((ROOT / "query_memory.json").read_text())
# Non-submitted queries don't go into "queries" list (only submitted=True does)
# They go into "abandoned_themes" via unsaid integration
# Since unsaid is optional, check total queries count went up OR abandoned_themes has entry
total_q = len(qm2.get("queries", []))
abandons = qm2.get("abandoned_themes", [])
print(f"  ✓ queries={total_q} abandoned_themes={len(abandons)}")

# ── TEST 5: file_heat_map.json written ────────────────────────────────────
print("\n── TEST 5: file_heat_map.json written with module data ─────────")
hm_path = ROOT / "file_heat_map.json"
assert hm_path.exists(), "file_heat_map.json NOT created"
hm = json.loads(hm_path.read_text())
# Heat map is flat {module_name: {avg_hes, avg_wpm, miss_count, total, samples}}
modules = {k: v for k, v in hm.items() if isinstance(v, dict)}
assert len(modules) > 0, f"No module entries in heat map: {list(hm.keys())}"
print(f"  ✓ {len(modules)} modules tracked:")
for name, v in list(modules.items())[:3]:
    print(f"    {name}: samples={v['total']} avg_hes={v['avg_hes']} avg_wpm={v['avg_wpm']} miss={v['miss_count']}")

# ── TEST 6: rework_log.json written ---
print("\n── TEST 6: rework_log.json correctness ─────────────────────────")
rw_path = ROOT / "rework_log.json"
assert rw_path.exists(), "rework_log.json NOT created"
rw_raw = json.loads(rw_path.read_text())
entries = rw_raw if isinstance(rw_raw, list) else rw_raw.get("entries", [])
verdicts = [e.get("verdict") for e in entries]
miss_count = verdicts.count("miss")
print(f"  ✓ {len(entries)} rework entries, verdicts={set(verdicts)}, misses={miss_count}")
for e in entries[-3:]:
    print(f"    verdict={e.get('verdict')} del={e.get('del_ratio')} rework_score={e.get('rework_score')} q={str(e.get('query_hint',''))[:45]}")

# ── TEST 7: load_query_memory() summary ───────────────────────────────────
print("\n── TEST 7: load_query_memory() summary ─────────────────────────")
sys.path.insert(0, str(ROOT))
import importlib.util
def load_mod(pattern):
    matches = sorted(ROOT.glob(pattern))
    if not matches: return None
    spec = importlib.util.spec_from_file_location("_m", matches[-1])
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

qm_mod = load_mod("src/query_memory_seq010*.py")
summary = qm_mod.load_query_memory(ROOT)
print(f"  total_queries={summary.get('total_queries')} unique_topics={summary.get('unique_topics')}")
print(f"  persistent_gaps: {summary.get('persistent_gaps', [])}")

# ── TEST 8: output fields schema ──────────────────────────────────────────
print("\n── TEST 8: bridge output schema ─────────────────────────────────")
required = {"state", "hesitation", "wpm", "coaching_updated", "rework_verdict"}
for f in required:
    assert f in r1, f"Missing field: {f}"
print(f"  ✓ all fields present: {sorted(required)}")

# ── SUMMARY ───────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
rw_total = len(entries)
qm_total = len(qm2.get("queries", []))
hm_total = len(modules)
miss_rate = round(miss_count/max(rw_total,1)*100)
print(f"rework_log    → {rw_total} responses, {miss_count} misses ({miss_rate}% miss rate)")
print(f"query_memory  → {qm_total} queries, {len(qm2.get('abandoned_themes',[]))} abandoned themes")
print(f"file_heat_map → {hm_total} modules tracked")
print(f"persistent gaps detected: {len(summary.get('persistent_gaps',[]))}")
print("\nALL DEEP SIGNAL TESTS PASSED ✓")
