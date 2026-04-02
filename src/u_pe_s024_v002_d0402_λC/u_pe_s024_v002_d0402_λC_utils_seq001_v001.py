"""u_pe_s024_v002_d0402_λC_utils_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

def _jload(path: Path):
    if not path.exists(): return None
    try: return json.loads(path.read_text('utf-8', errors='ignore'))
    except Exception: return None


def _jsonl(path: Path, n: int = 0) -> list:
    if not path.exists(): return []
    lines = path.read_text('utf-8', errors='ignore').strip().splitlines()
    if n: lines = lines[-n:]
    out = []
    for l in lines:
        try: out.append(json.loads(l))
        except Exception: pass
    return out
