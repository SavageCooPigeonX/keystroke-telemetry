"""u_pj_s019_v002_d0402_λC_system_state_seq008_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

def _active_tasks(root: Path) -> dict:
    """Summarize task queue state."""
    data = _load_json(root / TASK_PATH)
    if not data:
        return {'total': 0, 'in_progress': [], 'pending': 0}
    tasks = data if isinstance(data, list) else data.get('tasks', [])
    ip = [t.get('id', '?') for t in tasks if t.get('status') == 'in_progress']
    pending = sum(1 for t in tasks if t.get('status') == 'pending')
    done = sum(1 for t in tasks if t.get('status') == 'done')
    return {'total': len(tasks), 'in_progress': ip, 'pending': pending, 'done': done}


def _hot_modules(root: Path, top_n: int = 3) -> list[dict]:
    """Top N modules by hesitation from heat map."""
    data = _load_json(root / HEAT_PATH)
    if not data or not isinstance(data, dict):
        return []
    ranked = sorted(
        ((name, d.get('avg_hes', 0)) for name, d in data.items()
         if isinstance(d, dict) and d.get('total', 0) >= 2),
        key=lambda x: x[1], reverse=True
    )
    return [{'module': n, 'hes': round(h, 3)} for n, h in ranked[:top_n]]


def _mutation_count(root: Path) -> int:
    data = _load_json(root / MUTATIONS_PATH)
    if not data:
        return 0
    if isinstance(data, list):
        return len(data)
    return len(data.get('snapshots', []))


def _latest_runtime_module(root: Path, pattern: str) -> Path | None:
    matches = sorted(root.glob(pattern))
    return matches[-1] if matches else None
