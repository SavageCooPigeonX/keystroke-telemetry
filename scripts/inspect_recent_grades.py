"""Quick inspection of recent completion grades — see patterns in failures."""
import json
from pathlib import Path

lines = Path('logs/completion_grades.jsonl').read_text('utf-8').strip().splitlines()
gs = [json.loads(l) for l in lines[-40:]]
print(f'n={len(gs)}')
print(f'composite avg: {sum(g["composite"] for g in gs)/len(gs):.3f}')
print(f'relevance avg: {sum(g["relevance"] for g in gs)/len(gs):.3f}')
print(f'echo avg:      {sum(g["echo"] for g in gs)/len(gs):.3f}')
print(f'novelty avg:   {sum(g["novelty"] for g in gs)/len(gs):.3f}')
print()
print('RECENT 25:')
for g in gs[-25:]:
    head = g.get('completion_head', '')[:70]
    kw = ','.join(g.get('intent_keywords', [])[:4])
    print(f'  c={g["composite"]:.2f} rel={g["relevance"]:.2f} ech={g["echo"]:.2f} '
          f'nov={g["novelty"]:.2f} len={g["comp_len"]:>4} out={g["outcome"]:<9} '
          f'kw=[{kw}] :: "{head}"')
