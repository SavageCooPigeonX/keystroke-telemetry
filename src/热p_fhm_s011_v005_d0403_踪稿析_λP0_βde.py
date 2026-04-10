"""Per-file heat map — tracks Copilot edit frequency + entropy per module.

Mines edit_pairs.jsonl for which files Copilot actually touches, weighted by
recency. Cross-references entropy_map.json for uncertainty scores. The combined
signal tells the thought completer which files are actually hot — not which
files the operator hesitates on.

Reads edit_pairs.jsonl + entropy_map.json. Zero LLM calls.
"""
from __future__ import annotations
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

HEAT_STORE      = 'file_heat_map.json'
DECAY_HALF_LIFE = 86400 * 3  # 3 days — touches decay to half relevance
HIGH_VER_THRESH = 5


def update_heat_map(root: Path, **_kw) -> None:
    """Rebuild heat map from Copilot edit history + entropy scores.

    Reads edit_pairs.jsonl for touch counts with time-decay,
    reads entropy_map.json for per-module uncertainty.
    Combined: heat = decayed_touches * (1 + entropy).
    """
    touches = _count_copilot_touches(root)
    entropy = _load_entropy_scores(root)

    heat = {}
    for mod, touch_score in touches.items():
        ent = entropy.get(mod, 0.0)
        heat[mod] = {
            'touch_score': round(touch_score, 3),
            'entropy': round(ent, 3),
            'heat': round(touch_score * (1 + ent), 3),
        }

    # Add high-entropy modules even if Copilot hasn't touched them recently
    for mod, ent in entropy.items():
        if mod not in heat and ent > 0.3:
            heat[mod] = {
                'touch_score': 0.0,
                'entropy': round(ent, 3),
                'heat': round(0.1 * ent, 3),  # small base for untouched
            }

    heat_path = root / HEAT_STORE
    heat_path.write_text(json.dumps(heat, indent=2), encoding='utf-8')


def _count_copilot_touches(root: Path) -> dict[str, float]:
    """Count Copilot file touches from edit_pairs.jsonl with time decay."""
    ep = root / 'logs' / 'edit_pairs.jsonl'
    if not ep.exists():
        return {}

    now = datetime.now(timezone.utc)
    scores: dict[str, float] = {}

    try:
        for line in ep.read_text('utf-8', errors='ignore').splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except Exception:
                continue
            raw_file = entry.get('file', '')
            if not raw_file:
                continue
            stem = Path(raw_file).stem
            mod = re.split(r'_s(?:eq)?\d{3}', stem)[0]
            if not mod:
                continue

            # Time decay
            ts = entry.get('edit_ts', '')
            try:
                edit_time = datetime.fromisoformat(ts)
                age_s = (now - edit_time).total_seconds()
            except Exception:
                age_s = DECAY_HALF_LIFE * 2  # old if unparseable

            weight = math.exp(-0.693 * age_s / DECAY_HALF_LIFE)
            scores[mod] = scores.get(mod, 0.0) + weight
    except Exception:
        pass

    return scores


def _load_entropy_scores(root: Path) -> dict[str, float]:
    """Load per-module entropy from entropy_map.json."""
    ep = root / 'logs' / 'entropy_map.json'
    if not ep.exists():
        return {}
    try:
        data = json.loads(ep.read_text('utf-8', errors='ignore'))
        result = {}
        for m in data.get('top_entropy_modules', []):
            mod = m.get('module', '')
            if mod:
                result[mod] = m.get('avg_entropy', 0.0)
        return result
    except Exception:
        return {}


def load_heat_map(root: Path) -> dict:
    """Load file heat map → sorted list for coaching prompt."""
    heat_path = root / HEAT_STORE
    if not heat_path.exists():
        return {}
    try:
        heat = json.loads(heat_path.read_text('utf-8'))
    except Exception:
        return {}

    hot_files = [
        {'module': name, 'heat': d['heat'],
         'touches': d['touch_score'], 'entropy': d['entropy']}
        for name, d in heat.items()
    ]
    hot_files.sort(key=lambda x: x['heat'], reverse=True)

    return {
        'modules_tracked': len(heat),
        'hot_files': hot_files[:8],
    }


def load_registry_churn(root: Path) -> list[dict]:
    """Return top-churn modules from pigeon_registry for heat enrichment."""
    reg_path = root / 'pigeon_registry.json'
    if not reg_path.exists():
        return []
    try:
        reg = json.loads(reg_path.read_text('utf-8'))
    except Exception:
        return []
    files = reg.get('files', [])
    if not isinstance(files, list):
        files = [v for v in reg.values() if isinstance(v, dict)]
    entries = [
        {'module': e.get('name', ''), 'ver': e.get('ver', 1),
         'desc': e.get('desc', ''), 'tokens': e.get('tokens', 0)}
        for e in files
        if e.get('ver', 1) >= HIGH_VER_THRESH
    ]
    entries.sort(key=lambda x: x['ver'], reverse=True)
    return entries[:8]
