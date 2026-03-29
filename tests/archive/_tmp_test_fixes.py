"""Temporary test for classifier + rework fixes."""
import importlib, os, sys
from glob import glob
from pathlib import Path

sys.path.insert(0, '.')

# === CLASSIFIER TEST ===
hits = glob('src/operator_stats_seq008_v007*.py')
mod_name = 'src.' + os.path.splitext(os.path.basename(hits[0]))[0]
stats = importlib.import_module(mod_name)

baselines = {
    'n': 176, 'avg_wpm': 35.2, 'avg_del': 0.496, 'avg_hes': 0.695,
    'sd_wpm': 18.0, 'sd_del': 0.041, 'sd_hes': 0.039
}

tests = [
    {'total_keystrokes': 50, 'total_inserts': 25, 'total_deletions': 25,
     'hesitation_score': 0.700, 'effective_duration_ms': 30000,
     'typing_pauses': [{'duration_ms': 12000}],
     'desc': 'typical hes=0.700 del=50% pause=40%'},
    {'total_keystrokes': 80, 'total_inserts': 60, 'total_deletions': 20,
     'hesitation_score': 0.500, 'effective_duration_ms': 20000,
     'typing_pauses': [{'duration_ms': 5000}],
     'desc': 'fast focused (low hes, low del)'},
    {'total_keystrokes': 40, 'total_inserts': 15, 'total_deletions': 25,
     'hesitation_score': 0.850, 'effective_duration_ms': 45000,
     'typing_pauses': [{'duration_ms': 25000}],
     'desc': 'frustrated (high hes, high del, slow)'},
    {'total_keystrokes': 120, 'total_inserts': 100, 'total_deletions': 20,
     'hesitation_score': 0.300, 'effective_duration_ms': 15000,
     'typing_pauses': [{'duration_ms': 2000}],
     'desc': 'flow (fast, low error, low pause)'},
    {'total_keystrokes': 60, 'total_inserts': 35, 'total_deletions': 25,
     'hesitation_score': 0.720, 'effective_duration_ms': 35000,
     'typing_pauses': [{'duration_ms': 20000}],
     'desc': 'borderline (slightly above avg hes)'},
    {'total_keystrokes': 50, 'total_inserts': 25, 'total_deletions': 25,
     'hesitation_score': 0.700, 'effective_duration_ms': 30000,
     'typing_pauses': [{'duration_ms': 18000}],
     'desc': 'high pause=60% but normal hes'},
]

print("=== CLASSIFIER TEST (with actual baselines) ===")
print(f"SD floors: sd_hes=0.10 (was 0.01), sd_del=0.06 (was 0.01), sd_wpm=10.0 (was 1.0)")
print()
for t in tests:
    state = stats.classify_state(t, baselines)
    hes = t['hesitation_score']
    del_r = t['total_deletions'] / t['total_keystrokes']
    z_hes = (hes - baselines['avg_hes']) / max(baselines['sd_hes'], 0.10)
    z_del = (del_r - baselines['avg_del']) / max(baselines['sd_del'], 0.06)
    pause_r = sum(p['duration_ms'] for p in t['typing_pauses']) / t['effective_duration_ms']
    print(f"  {state:14s} z_hes={z_hes:+.2f} z_del={z_del:+.2f} pause={pause_r:.0%} | {t['desc']}")

# === REWORK SCORER TEST ===
print()
print("=== REWORK COMPOSITION SCORER TEST ===")
hits2 = glob('src/rework_detector_seq009*.py')
mod2 = 'src.' + os.path.splitext(os.path.basename(hits2[0]))[0]
rework = importlib.import_module(mod2)

compositions = [
    {'deletion_ratio': 0.0, 'rewrites': [], 'deleted_words': [],
     'total_keystrokes': 50, 'duration_ms': 10000,
     'desc': 'clean prompt (no deletions)'},
    {'deletion_ratio': 0.383, 'rewrites': [{'old': 'x', 'new': 'y'}],
     'deleted_words': [{'word': 'is that the best way'}],
     'total_keystrokes': 196, 'duration_ms': 39112,
     'desc': 'YOUR LAST PROMPT (38% del, 1 rewrite)'},
    {'deletion_ratio': 0.60, 'rewrites': [{'old': 'a', 'new': 'b'}, {'old': 'c', 'new': 'd'}],
     'deleted_words': [{'word': 'first attempt'}, {'word': 'no wait'}],
     'total_keystrokes': 300, 'duration_ms': 60000,
     'desc': 'heavy rework (60% del, 2 rewrites)'},
    {'deletion_ratio': 0.10, 'rewrites': [],
     'deleted_words': [{'word': 'typo'}],
     'total_keystrokes': 80, 'duration_ms': 15000,
     'desc': 'minor typo fix (10% del)'},
    {'deletion_ratio': 0.80, 'rewrites': [{'old': 'a', 'new': 'b'}, {'old': 'c', 'new': 'd'}, {'old': 'e', 'new': 'f'}],
     'deleted_words': [{'word': 'everything'}],
     'total_keystrokes': 400, 'duration_ms': 120000,
     'desc': 'total rewrite (80% del, 3 rewrites)'},
]

for c in compositions:
    result = rework.score_rework_from_composition(c)
    print(f"  {result['verdict']:8s} score={result['rework_score']:.3f} del={result['del_ratio']:.1%} | {c['desc']}")

# === EXISTING TESTS ===
print()
print("=== RUNNING test_all.py ===")
os.system('py test_all.py 2>&1')
