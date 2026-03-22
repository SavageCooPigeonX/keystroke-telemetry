"""dynamic_prompt_seq017_metrics_analysis_a_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
import json, re, subprocess

def _hot_modules(root):
    raw = _json(root / 'file_heat_map.json')
    if not raw or not isinstance(raw, dict): return []
    items = []
    for name, v in raw.items():
        if not isinstance(v, dict): continue
        samp = v.get('samples', [])
        if isinstance(samp, list):
            n = len(samp)
            if n < 2: continue
            hes = round(sum(s.get('hes', 0) for s in samp) / n, 3)
            miss = sum(1 for s in samp if s.get('verdict') == 'miss')
        else:
            n = samp
            if n < 2: continue
            hes = round(v.get('total_hes', 0) / max(n, 1), 3)
            miss = v.get('miss_count', 0)
        if hes > 0.4 or miss > 0:
            items.append({'m': name, 'h': hes, 'x': miss})
    return sorted(items, key=lambda x: x['h'], reverse=True)[:5]


def _rework(root):
    raw = _json(root / 'rework_log.json')
    if not raw: return {}
    entries = raw if isinstance(raw, list) else raw.get('entries', [])
    if not entries: return {}
    misses = [e for e in entries if e.get('verdict') == 'miss']
    return {'rate': round(len(misses) / max(len(entries), 1) * 100, 1),
            'n': len(entries),
            'worst': [e.get('query_text', '')[:60] for e in
                      sorted(misses, key=lambda e: e.get('rework_score', 0),
                             reverse=True)[:3]]}
