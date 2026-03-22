"""cognitive_reactor_seq014_state_ops_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

def _load_state(root: Path) -> dict:
    sp = root / STATE_FILE
    if sp.exists():
        try:
            return json.loads(sp.read_text('utf-8'))
        except Exception:
            pass
    return {'file_streaks': {}, 'last_fire': {}, 'total_fires': 0}


def _save_state(root: Path, state: dict):
    sp = root / STATE_FILE
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(json.dumps(state, indent=2), encoding='utf-8')
