"""Quick test for dossier scoring router."""
from pathlib import Path
import json, sys, importlib.util

root = Path('.')
p = sorted(root.glob('src/u_pe_s024*.py'))[-1]
spec = importlib.util.spec_from_file_location(p.stem, p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# Test 1: Bug-focused query
scored = m._score_bug_dossiers(root, 'fix the overcap bug in dynamic prompt')
print(f'Bug query: {len(scored)} dossiers scored')
for d in scored[:3]:
    print(f'  {d["file"]}: score={d["score"]} bugs={d["bugs"]}')

# Test 2: Generic query (should score low)
scored2 = m._score_bug_dossiers(root, 'what is next')
print(f'Generic query: {len(scored2)} dossiers')

# Test 3: Editor signal
scored3 = m._score_bug_dossiers(root, 'yes', open_files=['src/u_pe_s024_v003.py'])
print(f'Editor signal: {len(scored3)} dossiers')
for d in scored3[:2]:
    print(f'  {d["file"]}: score={d["score"]}')

# Test 4: Full dossier text generation
dossier = m._active_bug_dossier(root, 'fix the overcap bug', open_files=['src/u_pe_s024_v003.py'])
print(f'\nDossier text ({len(dossier)} chars):')
print(dossier[:300])

# Test 5: Check routing signal was written
sig = json.loads((root / 'logs' / 'active_dossier.json').read_text('utf-8'))
print(f'\nRouting signal: conf={sig["confidence"]}, focus={sig.get("focus_modules", [])[:3]}')

# Test 6: Rework feedback
p2 = sorted(root.glob('src/测p_rwd_s009*.py'))[-1]
spec2 = importlib.util.spec_from_file_location(p2.stem, p2)
m2 = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(m2)
m2._update_dossier_scores(root, 'ok')
print('\nRework feedback: applied ok verdict')
reg = json.loads((root / 'pigeon_registry.json').read_text('utf-8'))
files = reg if isinstance(reg, list) else reg.get('files', [])
for f in files:
    ds = f.get('dossier_score', 0)
    if ds != 0:
        print(f'  {f.get("file","?")}: dossier_score={ds}')
        break

print('\nAll tests passed.')
