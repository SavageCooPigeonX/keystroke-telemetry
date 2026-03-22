"""dynamic_prompt_seq017_profile_analysis_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
import json, re, subprocess

def _profile_history(root):
    p = root / 'operator_profile.md'
    if not p.exists(): return []
    m = re.search(r'<!--\s*\n?DATA\s*\n(.*?)\nDATA\s*\n-->',
                  p.read_text(encoding='utf-8', errors='ignore'), re.DOTALL)
    if not m: return []
    try: return json.loads(m.group(1).strip()).get('history', [])
    except Exception: return []


def _unsaid(comps):
    threads = []
    for c in comps[-8:]:
        for w in (c.get('deleted_words') or []):
            word = w.get('word', w) if isinstance(w, dict) else str(w)
            if word and len(word) > 3: threads.append(word)
    return threads[-6:]
