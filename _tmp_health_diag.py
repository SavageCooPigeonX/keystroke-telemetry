"""Quick health diagnosis."""
from _build_organism_health import _compliance_scan, _count_py_files, _load_json, _load_jsonl
from pathlib import Path
root = Path('.')

total, compliant, over = _compliance_scan(root)
print(f'=== COMPLIANCE ===')
print(f'Total: {total}  Compliant: {compliant}  Over: {len(over)}')
print(f'Rate: {compliant/total*100:.1f}%')
print()
ranges = {'201-300': 0, '301-500': 0, '501-1000': 0, '1000+': 0}
for f, lc in over:
    if lc <= 300: ranges['201-300'] += 1
    elif lc <= 500: ranges['301-500'] += 1
    elif lc <= 1000: ranges['501-1000'] += 1
    else: ranges['1000+'] += 1
for r, n in ranges.items():
    print(f'  {r}: {n} files')

print()
print('=== TOP 20 OVER-CAP ===')
for f, lc in over[:20]:
    print(f'  {lc:5d}  {f}')

print()
veins = _load_json(root / 'pigeon_brain/context_veins.json')
if veins:
    clots = veins.get('clots', [])
    print(f'=== CLOTS: {len(clots)} ===')
    for c in clots[:10]:
        mod = c.get('module', '?')
        sigs = c.get('clot_signals', [])
        print(f'  {mod:50s} {sigs}')

print()
rework = _load_json(root / 'rework_log.json') or []
reworked = sum(1 for r in rework if r.get('rework_score', 0) > 0)
print(f'=== REWORK: {reworked}/{len(rework)} ({reworked/len(rework)*100:.0f}%) ===')

deaths = _load_json(root / 'execution_death_log.json') or []
print(f'=== DEATHS: {len(deaths)} total ===')
for d in deaths[-5:]:
    print(f'  {d.get("module","?"):30s} {d.get("cause","?")} severity={d.get("severity","?")}')

# What monolith .py files have corresponding decomposed packages?
print()
print('=== MONOLITH + PACKAGE DUPLICATES ===')
src = root / 'src'
dupes = []
for f in src.iterdir():
    if f.is_file() and f.suffix == '.py' and f.stem != '__init__':
        pkg = src / f.stem
        if pkg.is_dir() and (pkg / '__init__.py').exists():
            lines = len(f.read_text('utf-8', errors='ignore').splitlines())
            if lines > 200:
                dupes.append((f.stem, lines))
for name, lines in sorted(dupes, key=lambda x: -x[1]):
    print(f'  {lines:5d}  {name} (monolith still exists alongside package)')
