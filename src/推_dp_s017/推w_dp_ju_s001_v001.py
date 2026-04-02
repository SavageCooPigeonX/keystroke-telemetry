"""dynamic_prompt_seq017_json_utils_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
import json, re, subprocess

def _jsonl(path, n=0):
    if not path.exists(): return []
    ll = path.read_text(encoding='utf-8', errors='ignore').strip().splitlines()
    if n: ll = ll[-n:]
    out = []
    for l in ll:
        try: out.append(json.loads(l))
        except Exception: pass
    return out


def _json(path):
    if not path.exists(): return None
    try: return json.loads(path.read_text(encoding='utf-8', errors='ignore'))
    except Exception: return None
