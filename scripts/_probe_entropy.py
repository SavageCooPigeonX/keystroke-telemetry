import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / 'src'))
from entropy_shedding_seq001_v001 import accumulate_entropy
r = accumulate_entropy('.')
print('global H:', r['global_avg_entropy'])
print('tracked:', r['tracked_modules'], 'edit_pair_modules:', r['edit_pair_modules'])
print('--- top 12 after fix ---')
for m in r['top_entropy_modules'][:12]:
    print(f"  {m['module']:42s} H={m['avg_entropy']:.3f} samples={m['samples']} edit={m['edit_samples']}")
print('--- red top 12 ---')
for row in r['red_layer'][:12]:
    print(f"  {row['module']:42s} red={row['red']:.3f}")
