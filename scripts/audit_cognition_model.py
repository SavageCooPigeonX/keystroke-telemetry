"""Audit the numeric cognition model: vocab, matrix, touches, per-file storage, self-model accuracy."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent.parent

# 1. Numeric cognition model
vocab_raw = json.loads((root/'logs/intent_vocab.json').read_text('utf-8'))
vocab = vocab_raw.get('word_to_id', vocab_raw) if isinstance(vocab_raw, dict) else {}
matrix_raw = json.loads((root/'logs/intent_matrix.json').read_text('utf-8'))
matrix = matrix_raw.get('matrix', matrix_raw) if isinstance(matrix_raw, dict) else {}
touches_path = root/'logs/intent_touches.jsonl'
touches = touches_path.read_text('utf-8').strip().splitlines() if touches_path.exists() else []

print('=== NUMERIC COGNITION MODEL ===')
print(f'  vocab size       : {len(vocab)} words')
print(f'  matrix files     : {len(matrix)} files with learned weights')
print(f'  training touches : {len(touches)} prompt->file pairs')
if matrix:
    sizes = sorted([(k, len(v)) for k,v in matrix.items() if isinstance(v, dict)], key=lambda x: -x[1])
    print(f'  top learned files by vocab richness:')
    for k,n in sizes[:8]:
        print(f'    {k}: {n} word associations')

# 2. Per-file prompt storage
print()
print('=== PER-FILE PROMPT STORAGE ===')
for sub in ['file_memories', 'module_memory', 'module_pitches', 'probes']:
    p = root/'logs'/sub
    if p.exists():
        items = list(p.iterdir())
        print(f'  logs/{sub}/       : {len(items)} items')
        for s in items[:3]:
            print(f'    {s.name} ({s.stat().st_size}B)')
    else:
        print(f'  logs/{sub}/       : MISSING')

# 3. Self_fix accuracy: who has most accurate self-model
acc_path = root/'logs/self_fix_accuracy.json'
if acc_path.exists():
    acc = json.loads(acc_path.read_text('utf-8'))
    print()
    print('=== SELF_FIX ACCURACY TRACKER ===')
    if isinstance(acc, dict):
        print(f'  top-level keys: {list(acc.keys())[:20]}')
        # Try to detect per-module accuracy
        for k,v in list(acc.items())[:5]:
            preview = str(v)[:250]
            print(f'  [{k}] -> {preview}')

# 4. Bug profiles: who has bugs vs who claims they don't
bp_path = root/'logs/bug_profiles.json'
if bp_path.exists():
    bp = json.loads(bp_path.read_text('utf-8'))
    print()
    print('=== BUG PROFILES (declared vs actual) ===')
    if isinstance(bp, dict):
        profiles = bp.get('profiles', bp) if 'profiles' in bp else bp
        if isinstance(profiles, dict):
            n = len(profiles)
            with_bugs = sum(1 for v in profiles.values() if isinstance(v, dict) and v.get('bugs'))
            print(f'  profiles: {n}, with declared bugs: {with_bugs}')
            # Example
            for name, prof in list(profiles.items())[:3]:
                if isinstance(prof, dict):
                    print(f'  {name}: {list(prof.keys())[:8]}')

# 5. Verify predict_files works on a current prompt
print()
print('=== LIVE PREDICTION TEST ===')
import sys
sys.path.insert(0, str(root))
try:
    from src.intent_numeric import predict_files, get_stats
    stats = get_stats()
    print(f'  stats: {stats}')
    test_prompts = [
        "test gemini key after rotation",
        "audit bug profiles numeric encoding",
        "push cycle rename engine self fix",
    ]
    for p in test_prompts:
        try:
            preds = predict_files(p, top_n=5)
            print(f'  "{p[:40]}" -> {[(f, round(s,3)) for f,s in preds[:5]]}')
        except Exception as e:
            print(f'  "{p[:40]}" FAILED: {e}')
except Exception as e:
    print(f'  IMPORT FAILED: {e}')
