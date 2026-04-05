"""Debug: why composition binding is failing."""
import json, time
from pathlib import Path
from datetime import datetime, timezone

root = Path('.')

# Load latest compositions
comps_path = root / 'logs' / 'chat_compositions.jsonl'
prompt_comps_path = root / 'logs' / 'prompt_compositions.jsonl'

def read_last_n(path, n=5):
    if not path.exists():
        return []
    lines = path.read_text('utf-8', errors='ignore').strip().splitlines()
    entries = []
    for line in lines[-n:]:
        try:
            entries.append(json.loads(line))
        except:
            pass
    return entries

# The exact prompt text Copilot sends
test_msg = "interesting - so it looks like copilot injextion is i prompt delayed/ lets test deleted word: - checkif gemini reohraser triggers in cot -"

print(f"TEST MSG: {test_msg[:80]}...")
print(f"MSG LEN: {len(test_msg)}")
print()

# Check last compositions
for source, path in [('prompt_compositions', prompt_comps_path), ('chat_compositions', comps_path)]:
    entries = read_last_n(path, 5)
    print(f"=== {source}: {len(entries)} recent entries ===")
    for i, e in enumerate(entries):
        # Get the text that would be matched against
        final_text = e.get('final_text', e.get('text', e.get('buffer', '')))
        ts = e.get('ts', e.get('last_key_ts', '?'))
        if isinstance(ts, (int, float)):
            from datetime import datetime as dt
            ts_str = dt.fromtimestamp(ts/1000, tz=timezone.utc).isoformat()[:19]
        else:
            ts_str = str(ts)[:19]

        # Compute match score manually
        import re
        def _normalize(text):
            return re.sub(r'\s+', ' ', str(text).lower().strip())

        def _token_set(text):
            return set(re.findall(r'\b\w+\b', text))

        msg_norm = _normalize(test_msg)
        comp_norm = _normalize(final_text)

        if msg_norm == comp_norm:
            score = 1.0
        else:
            msg_tokens = _token_set(msg_norm)
            comp_tokens = _token_set(comp_norm)
            if msg_tokens and comp_tokens:
                overlap = len(msg_tokens & comp_tokens) / max(len(msg_tokens | comp_tokens), 1)
                containment = 1.0 if msg_norm in comp_norm or comp_norm in msg_norm else 0.0
                score = max(overlap, containment)
            else:
                score = 0.0

        keys = e.get('total_keystrokes', 0)
        dw = e.get('deleted_words', [])
        dw_words = [w.get('word', w) if isinstance(w, dict) else w for w in dw]

        print(f"  [{i}] ts={ts_str} keys={keys} score={score:.3f}")
        print(f"      text: {comp_norm[:80]}")
        print(f"      deleted: {dw_words}")
        print(f"      match tokens: {len(_token_set(msg_norm) & _token_set(comp_norm))}/{len(_token_set(msg_norm) | _token_set(comp_norm))}")

        # Check age
        now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        comp_ts = None
        for field in ['last_key_ts', 'first_key_ts', 'ts']:
            val = e.get(field)
            if isinstance(val, (int, float)) and val > 1e12:
                comp_ts = int(val)
                break
            if isinstance(val, str):
                try:
                    dt_obj = datetime.fromisoformat(val)
                    comp_ts = int(dt_obj.timestamp() * 1000)
                    break
                except:
                    pass
        if comp_ts:
            age_ms = now_ms - comp_ts
            print(f"      age: {age_ms/1000:.1f}s ({age_ms/60000:.1f}min)")
        print()
