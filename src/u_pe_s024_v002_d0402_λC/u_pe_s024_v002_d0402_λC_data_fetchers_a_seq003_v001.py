"""u_pe_s024_v002_d0402_λC_data_fetchers_a_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

def _hot_files(root: Path, top_n: int = 5) -> list[dict]:
    """Return top N files by hesitation score from file_heat_map."""
    raw = _jload(root / 'file_heat_map.json')
    if not raw or not isinstance(raw, dict): return []
    items = []
    for name, v in raw.items():
        if not isinstance(v, dict): continue
        hes = v.get('avg_hes', 0)
        touches = v.get('total', 0)
        if touches >= 2:
            items.append({'file': name, 'hes': round(hes, 3), 'touches': touches})
    return sorted(items, key=lambda x: x['hes'], reverse=True)[:top_n]


def _registry_touches(root: Path, query: str) -> list[dict]:
    """Find registry entries for modules mentioned in the query."""
    reg = _jload(root / 'pigeon_registry.json')
    if not reg: return []
    files = reg if isinstance(reg, list) else reg.get('files', [])
    query_lower = query.lower()
    hits = []
    for f in files:
        name = f.get('file', '') or f.get('desc', '')
        seq = f.get('seq', '')
        if any(part in query_lower for part in name.lower().split('_') if len(part) > 3):
            hits.append({
                'file': name,
                'ver': f.get('ver', '?'),
                'desc': f.get('desc', ''),
                'intent': f.get('intent', ''),
            })
    return hits[:4]


def _cognitive_state(root: Path) -> dict:
    snap = _jload(root / 'logs' / 'prompt_telemetry_latest.json')
    if not snap: return {}
    signals = snap.get('signals', {})
    summary = snap.get('running_summary', {})
    return {
        'state': summary.get('dominant_state', 'unknown'),
        'wpm': signals.get('wpm', 0),
        'del_ratio': signals.get('deletion_ratio', 0),
        'hes': signals.get('hesitation_count', 0),
    }
