"""Cross-signal analysis: entropy × heat × rework × profiles × registry."""
import json
from pathlib import Path
from collections import Counter, defaultdict

root = Path('.')

entropy = json.loads((root / 'logs/entropy_map.json').read_text('utf-8'))
heat = json.loads((root / 'file_heat_map.json').read_text('utf-8'))
rework = json.loads((root / 'rework_log.json').read_text('utf-8'))
profiles = json.loads((root / 'file_profiles.json').read_text('utf-8')) if (root / 'file_profiles.json').exists() else {}
registry = json.loads((root / 'pigeon_registry.json').read_text('utf-8'))
reg_files = registry.get('files', []) if isinstance(registry, dict) else registry

# Build lookup tables
red_lookup = {r['module']: r for r in entropy.get('red_layer', [])}
ent_lookup = {e['module']: e for e in entropy.get('top_entropy_modules', [])}

print('=' * 70)
print('SIGNAL ANALYSIS: what the data says that nothing is computing')
print('=' * 70)

# ── 1. REWORK STALE SIGNAL ──
print('\n─── 1. REWORK SIGNAL STALENESS ───')
scores = [(r['rework_score'], r['del_ratio'], r['wpm']) for r in rework]
# detect consecutive identical entries (stale/frozen sensor)
stale_runs = []
run_start = 0
for i in range(1, len(rework)):
    if (rework[i]['rework_score'] == rework[i-1]['rework_score'] and
        rework[i]['del_ratio'] == rework[i-1]['del_ratio'] and
        rework[i]['wpm'] == rework[i-1]['wpm']):
        continue
    else:
        run_len = i - run_start
        if run_len >= 3:
            stale_runs.append((run_start, run_len, rework[run_start]['rework_score']))
        run_start = i
# check last run
run_len = len(rework) - run_start
if run_len >= 3:
    stale_runs.append((run_start, run_len, rework[run_start]['rework_score']))

total_stale = sum(r[1] for r in stale_runs)
print(f'  total rework entries: {len(rework)}')
print(f'  stale runs (3+ identical consecutive): {len(stale_runs)}')
print(f'  entries in stale runs: {total_stale}/{len(rework)} ({100*total_stale/max(len(rework),1):.0f}%)')
for s in stale_runs[:5]:
    print(f'    index {s[0]}–{s[0]+s[1]-1}: score={s[2]}, length={s[1]}')

# ── 2. ENTROPY × HEAT DIVERGENCE ──
print('\n─── 2. ENTROPY × HEAT DIVERGENCE (blind spots) ───')
print('  modules with high heat but NO entropy signal:')
sorted_heat = sorted(heat.items(), key=lambda x: -x[1].get('heat', 0))
for name, h in sorted_heat:
    if h.get('heat', 0) > 0.2 and h.get('entropy', 0) == 0:
        ent = ent_lookup.get(name, {})
        beh_h = ent.get('avg_entropy', 0) if ent else 0
        red = red_lookup.get(name, {}).get('red', 0)
        print(f'    {name}: heat={h["heat"]:.3f} touch={h["touch_score"]:.3f} behavioral_H={beh_h:.3f} red={red:.3f}')

print('\n  modules with high entropy but NEVER touched (neglected uncertainty):')
for e in entropy.get('top_entropy_modules', [])[:20]:
    name = e['module']
    h = heat.get(name, {})
    if e['avg_entropy'] > 0.33 and h.get('heat', 0) < 0.05:
        print(f'    {name}: H={e["avg_entropy"]:.3f} heat={h.get("heat",0):.3f} samples={e["samples"]}')

# ── 3. SHED vs BEHAVIORAL ENTROPY CONTRADICTION ──
print('\n─── 3. SHED vs BEHAVIORAL CONTRADICTION ───')
print('  modules where shed confidence DISAGREES with behavioral entropy:')
for e in entropy.get('top_entropy_modules', []):
    if e.get('shed_avg_confidence') is not None and e['samples'] > 0:
        shed_ent = 1.0 - e['shed_avg_confidence']
        beh_ent = e['avg_entropy']
        delta = abs(shed_ent - beh_ent)
        if delta > 0.15:
            direction = 'overconfident' if shed_ent < beh_ent else 'underconfident'
            print(f'    {e["module"]}: shed says conf={e["shed_avg_confidence"]:.2f} (ent={shed_ent:.2f}) but behavior shows H={beh_ent:.3f} → {direction} by {delta:.2f}')

# ── 4. GHOST MODULES in entropy map ──
print('\n─── 4. GHOST MODULES (in entropy but not in registry) ───')
reg_names = set()
for f in reg_files:
    reg_names.add(f.get('name', ''))
    reg_names.add(Path(f.get('path', '')).stem)
    reg_names.add(f.get('desc', ''))

ghosts = []
for e in entropy.get('red_layer', []):
    name = e['module']
    if name not in reg_names and not name.endswith('.py') and not name.endswith('.jsonl'):
        ghosts.append((name, e['red']))
if ghosts:
    for g in ghosts[:10]:
        print(f'    {g[0]}: red={g[1]:.3f} (exists in entropy map but no registry entry)')
else:
    print('    none found')

# ── 5. HEAT MAP ENTROPY COMPONENT NEVER POPULATED ──
print('\n─── 5. HEAT MAP ENTROPY COMPONENT ───')
has_entropy = sum(1 for h in heat.values() if h.get('entropy', 0) > 0)
total_heat = len(heat)
print(f'  modules with entropy > 0 in heat map: {has_entropy}/{total_heat}')
if has_entropy > 0:
    for name, h in sorted(heat.items(), key=lambda x: -x[1].get('entropy', 0)):
        if h.get('entropy', 0) > 0:
            print(f'    {name}: entropy={h["entropy"]:.3f} touch={h["touch_score"]:.3f}')

# ── 6. REWORK VERDICT × TIME-OF-DAY ──
print('\n─── 6. REWORK × TIME PATTERN ───')
from datetime import datetime
hour_verdicts = defaultdict(lambda: {'ok': 0, 'miss': 0, 'partial': 0})
for r in rework:
    try:
        ts = datetime.fromisoformat(r['ts'])
        hour = ts.hour
        hour_verdicts[hour][r['verdict']] += 1
    except Exception:
        pass
if hour_verdicts:
    print('  hour  ok  miss  partial  miss_rate')
    for h in sorted(hour_verdicts):
        v = hour_verdicts[h]
        total = v['ok'] + v['miss'] + v['partial']
        rate = v['miss'] / max(total, 1)
        bar = '#' * int(rate * 20)
        print(f'  {h:02d}    {v["ok"]:3d}  {v["miss"]:4d}  {v["partial"]:7d}  {rate:.0%} {bar}')

# ── 7. PROFILE VERSION × ENTROPY correlation ──
print('\n─── 7. VERSION CHURN × ENTROPY ───')
version_entropy = []
for f in reg_files:
    ver = f.get('ver', 0) or 0
    name = f.get('name', '')
    ent = ent_lookup.get(name, {})
    red_e = red_lookup.get(name, {})
    beh_h = ent.get('avg_entropy', 0) if ent else 0
    red_score = red_e.get('red', 0) if red_e else 0
    h = heat.get(name, {})
    heat_score = h.get('heat', 0) if h else 0
    if ver > 0:
        version_entropy.append((name, ver, beh_h, red_score, heat_score))

version_entropy.sort(key=lambda x: -x[1])
print('  top churn modules (most versions):')
for name, ver, beh, red, ht in version_entropy[:15]:
    signals = []
    if beh > 0.3: signals.append(f'H={beh:.2f}')
    if red > 0.3: signals.append(f'red={red:.2f}')
    if ht > 0.3: signals.append(f'heat={ht:.2f}')
    sig_str = ' | '.join(signals) if signals else 'no signal'
    print(f'    {name} v{ver}: {sig_str}')

# Low churn + high entropy = surprising
print('\n  LOW churn but HIGH entropy (surprising uncertainty):')
for name, ver, beh, red, ht in version_entropy:
    if ver <= 2 and (beh > 0.33 or red > 0.35):
        print(f'    {name} v{ver}: H={beh:.3f} red={red:.3f}')

# ── 8. TOKEN SIZE × ENTROPY ──
print('\n─── 8. TOKEN SIZE × ENTROPY (complexity correlation) ───')
size_ent = []
for f in reg_files:
    name = f.get('name', '')
    tokens = f.get('tokens', 0) or 0
    ent = ent_lookup.get(name, {})
    beh = ent.get('avg_entropy', 0) if ent else 0
    size_ent.append((name, tokens, beh))

# big files with low entropy = confident complexity
big_low = [(n, t, e) for n, t, e in size_ent if t > 2000 and e < 0.1]
print(f'  large files (>2000 tok) with LOW entropy (<0.1): {len(big_low)}')
for n, t, e in sorted(big_low, key=lambda x: -x[1])[:5]:
    print(f'    {n}: {t} tokens, H={e:.3f}')

# small files with high entropy = small but confusing
small_high = [(n, t, e) for n, t, e in size_ent if 0 < t < 800 and e > 0.33]
print(f'  small files (<800 tok) with HIGH entropy (>0.33): {len(small_high)}')
for n, t, e in sorted(small_high, key=lambda x: -x[2])[:5]:
    print(f'    {n}: {t} tokens, H={e:.3f}')

# ── 9. REWORK QUERY_HINT CLUSTERING ──
print('\n─── 9. REWORK QUERY CLUSTERING ───')
bg_contexts = Counter()
for r in rework:
    hint = r.get('query_hint', '')
    if hint.startswith('bg:'):
        ctx = hint[3:].strip()[:60]
        bg_contexts[ctx] += 1

print('  background context during rework events:')
for ctx, count in bg_contexts.most_common(5):
    misses = sum(1 for r in rework if r.get('query_hint', '').startswith(f'bg:{ctx}') and r['verdict'] == 'miss')
    safe_ctx = ctx.encode('ascii', errors='replace').decode('ascii')
    print(f'    "{safe_ctx}": {count} events ({misses} misses)')

# ── 10. UNTAPPED SIGNAL: files that exist but have ZERO presence ──
print('\n─── 10. DARK MATTER (registry files with zero signal anywhere) ───')
dark = []
for f in reg_files:
    name = f.get('name', '')
    if not name:
        continue
    in_heat = name in heat
    in_ent = name in ent_lookup or name in red_lookup
    in_rework = any(name in r.get('query_hint', '') for r in rework[-50:])
    if not in_heat and not in_ent and not in_rework:
        dark.append(name)

print(f'  {len(dark)}/{len(reg_files)} files have NO signal in heat/entropy/rework')
if dark:
    print(f'  sample: {", ".join(dark[:10])}')
