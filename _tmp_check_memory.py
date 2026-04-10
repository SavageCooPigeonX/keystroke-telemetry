import json
from pathlib import Path

nm = json.loads(Path('pigeon_brain/node_memory.json').read_text('utf-8'))
print(f'Total nodes: {len(nm)}')

for name in ['file_heat_map', 'models', 'logger', 'operator_stats', 'push_narrative']:
    node = nm.get(name, {})
    entries = node.get('entries', [])
    print(f'{name}: samples={len(entries)}, rolling={node.get("rolling_score", 0):.4f}')
    if entries:
        last = entries[-1]
        print(f'  latest: score={last.get("score", 0):.3f}, ts={last.get("ts", "?")}')

# Check module_state for chat-based learning
state_dir = Path('logs/module_state')
if state_dir.exists():
    states = list(state_dir.glob('*.json'))
    print(f'\nModule state files: {len(states)}')
    for s in sorted(states)[:10]:
        data = json.loads(s.read_text('utf-8'))
        count = data.get('conversation_count', 0)
        if count > 0:
            print(f'  {s.stem}: {count} conversations')
