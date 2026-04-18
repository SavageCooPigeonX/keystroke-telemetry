"""Quick test: verify comedy system prompt generation."""
import sys, json
sys.path.insert(0, '.')
from src.profile_chat_server_seq001_v001_seq001_v001 import _build_system_prompt, _load_identities

ids = _load_identities()
for name, ident in ids.items():
    if ident.get('bugs') or ident.get('deaths'):
        print(f'=== TESTING: {name} ===')
        print(f'archetype={ident["archetype"]} emotion={ident["emotion"]}')
        print(f'bugs={ident.get("bugs",[])} deaths={len(ident.get("deaths",[]))}')
        print(f'backstory={ident.get("backstory",[])}')
        print(f'coaching={ident.get("coaching",[])}')
        print()
        prompt = _build_system_prompt(ident, {'conversation_count': 3})
        rules_start = prompt.find('== BACKSTORY ==')
        if rules_start > 0:
            print(prompt[rules_start:])
        else:
            print(prompt[-1200:])
        break
