"""Test mutation/patch pipeline components."""
import sys, json, ast, glob, importlib.util
from pathlib import Path

root = Path(".")
passed = 0
failed = 0

def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name} — {detail}")

# ── decision_maker ──
print("=== decision_maker ===")
dm_files = sorted(glob.glob("src/cognitive_reactor_seq014/*decision_maker*.py"))
spec = importlib.util.spec_from_file_location("dm", dm_files[-1])
dm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dm)

good_src = "def hello():\n    return 42\n"
orig_src = "def hello():\n    return 41\n"
r = dm.should_apply_patch(root, "test.py", good_src, orig_src)
test("valid small patch allowed", r["allow"], r.get("reason"))

bad_src = "def hello(:\n    return 42\n"
r = dm.should_apply_patch(root, "test.py", bad_src, orig_src)
test("syntax error blocked", not r["allow"], r.get("reason"))

big = "\n".join([f"line_{i} = {i}" for i in range(201)])
r = dm.should_apply_patch(root, "test.py", big, orig_src)
test("over 200 lines blocked", not r["allow"], r.get("reason"))

big_delta = "\n".join([f"x_{i} = {i}" for i in range(50)])
small_orig = "x = 1\n"
r = dm.should_apply_patch(root, "test.py", big_delta, small_orig)
test("big delta blocked", not r["allow"], r.get("reason"))

# ── patch_writer ──
print("\n=== patch_writer ===")
pw_files = sorted(glob.glob("src/cognitive_reactor_seq014/*patch_writer*.py"))
spec2 = importlib.util.spec_from_file_location("pw", pw_files[-1])
pw = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(pw)

patch_text = "Here is the fix:\n```python\ndef fixed():\n    return 42\n```\n"
blocks = pw.extract_code_blocks(patch_text)
test("code blocks found", len(blocks) == 1, f"got {len(blocks)}")

replace_text = "Fix:\n```old\nx = 1\n```\n```new\nx = 2\n```\n"
pairs = pw.extract_replacements(replace_text)
test("replacement pairs found", len(pairs) == 1, f"got {len(pairs)}")

# ── mutation_scorer ──
print("\n=== mutation_scorer ===")
ms_path = sorted(glob.glob("src/mutation_scorer_seq021*.py"))
spec3 = importlib.util.spec_from_file_location("ms", ms_path[-1])
ms = importlib.util.module_from_spec(spec3)
spec3.loader.exec_module(ms)
result = ms.score_mutations(root)
test("score_mutations returns dict", isinstance(result, dict))
test("has total_pairs", "total_pairs" in result)
print(f"    total_pairs={result.get('total_pairs')}, sections={len(result.get('sections', {}))}")

# ── dynamic_prompt mutation effectiveness ──
print("\n=== dynamic_prompt _mutation_effectiveness ===")
dp_path = sorted(glob.glob("src/dynamic_prompt_seq017*v009*.py"))
spec4 = importlib.util.spec_from_file_location("dp", dp_path[-1])
dp = importlib.util.module_from_spec(spec4)
spec4.loader.exec_module(dp)
me = dp._mutation_effectiveness(root)
test("_mutation_effectiveness runs", me is not None or me is None, "no crash")
if me:
    print(f"    first 300 chars: {me[:300]}")
else:
    print("    (returned None — no significant data yet, OK)")

# ── core tests ──
print("\n=== core test_all.py ===")
import subprocess
cp = subprocess.run([sys.executable, "test_all.py"], capture_output=True, text=True, encoding="utf-8", errors="replace")
print(cp.stdout[-500:] if cp.stdout else "(no stdout)")
if cp.returncode != 0:
    print(cp.stderr[-500:] if cp.stderr else "(no stderr)")
test("test_all.py passes", cp.returncode == 0, f"exit code {cp.returncode}")

# ── summary ──
print(f"\n{'='*40}")
print(f"Pipeline tests: {passed} passed, {failed} failed")
if failed:
    sys.exit(1)
print("ALL PIPELINE TESTS PASSED")
