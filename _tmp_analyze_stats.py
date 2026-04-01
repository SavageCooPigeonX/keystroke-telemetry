import json

d = json.loads(open('build/compressed/STATS.json').read())
af = d['all_files']

# Histogram
buckets = {}
for f in af:
    r = f['ratio']
    if r < 1.0: b = '<1.0'
    elif r < 1.2: b = '1.0-1.2'
    elif r < 1.5: b = '1.2-1.5'
    elif r < 2.0: b = '1.5-2.0'
    elif r < 3.0: b = '2.0-3.0'
    elif r < 5.0: b = '3.0-5.0'
    else: b = '5.0+'
    buckets[b] = buckets.get(b, 0) + 1

print("=== COMPRESSION DISTRIBUTION ===")
for b in ['<1.0', '1.0-1.2', '1.2-1.5', '1.5-2.0', '2.0-3.0', '3.0-5.0', '5.0+']:
    c = buckets.get(b, 0)
    bar = '#' * c
    print(f'{b:>8}: {c:>4} {bar}')

print(f"\nTotal: {len(af)} files")

# Tokens by bucket
print("\n=== TOKEN DISTRIBUTION ===")
for b in ['<1.0', '1.0-1.2', '1.2-1.5', '1.5-2.0', '2.0-3.0', '3.0-5.0', '5.0+']:
    orig = sum(f['orig_tokens'] for f in af if
               (b == '<1.0' and f['ratio'] < 1.0) or
               (b == '1.0-1.2' and 1.0 <= f['ratio'] < 1.2) or
               (b == '1.2-1.5' and 1.2 <= f['ratio'] < 1.5) or
               (b == '1.5-2.0' and 1.5 <= f['ratio'] < 2.0) or
               (b == '2.0-3.0' and 2.0 <= f['ratio'] < 3.0) or
               (b == '3.0-5.0' and 3.0 <= f['ratio'] < 5.0) or
               (b == '5.0+' and f['ratio'] >= 5.0))
    print(f'{b:>8}: {orig:>8,} orig tokens')

print("\n=== WORST 15 FILES ===")
worst = sorted(af, key=lambda x: x['ratio'])[:15]
for s in worst:
    print(f"  {s['ratio']:5.2f}x  {s['orig_tokens']:>6} -> {s['new_tokens']:>6}  {s['file'][:70]}")
