import json
data = json.load(open('pigeon_registry.json', 'r', encoding='utf-8'))
files = data.get('files', [])
dupes = [f for f in files if 'copilot_prompt' in f.get('name', '')]
print(f'{len(dupes)} copilot_prompt entries:')
for d in dupes:
    print(f"  {d['name']} | {d.get('path','')}")

# Also test _extract_mentions with a real buffer
import sys, os
sys.path.insert(0, '.')
from src.tc_context_seq001_v001_seq001_v001_agent_seq001_v001_seq001_v001 import _extract_mentions, _STOPWORDS
test_buf = "would it make sense for the thought completer to have awarness"
mentions = _extract_mentions(test_buf)
print(f"\nbuffer: '{test_buf}'")
print(f"mentions extracted: {mentions}")
print(f"total stopwords: {len(_STOPWORDS)}")

# Show which words got filtered
import re
words = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*', test_buf.lower())
for w in words:
    if len(w) > 4:
        status = "BLOCKED" if w in _STOPWORDS else "PASSED"
        print(f"  {w}: {status}")
