"""叙p_pn_s012_v008_d0403_初写谱净拆_λP0_βoc_load_composition_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import os

def _load_composition_snapshot(root: Path) -> dict | None:
    log = root / 'logs' / 'prompt_compositions.jsonl'
    if not log.exists(): return None
    try:
        lines = log.read_text(encoding='utf-8').strip().splitlines()
        return json.loads(lines[-1]) if lines else None
    except Exception: return None
