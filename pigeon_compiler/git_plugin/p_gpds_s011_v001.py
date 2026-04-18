"""git_plugin_deep_signals_seq011_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 011 | VER: v001 | 68 lines | ~808 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import os
import re

def _load_deep_signals(root: Path) -> dict:
    """Load rework, query memory, and heat map stores for narrative + coaching."""
    signals: dict = {}
    try:
        rw_path = root / 'rework_log.json'
        if rw_path.exists():
            raw = json.loads(rw_path.read_text('utf-8'))
            entries = raw if isinstance(raw, list) else raw.get('entries', [])
            total = len(entries)
            misses = [e for e in entries if e.get('verdict') == 'miss']
            miss_rate = round(len(misses) / max(total, 1), 3)
            worst = sorted(misses, key=lambda e: e.get('rework_score', 0), reverse=True)
            signals['rework'] = {
                'miss_rate': miss_rate, 'miss_count': len(misses),
                'total_responses': total,
                'worst_queries': [e.get('query_text', '')[:60] for e in worst[:3]],
            }
    except Exception:
        pass
    try:
        qm_path = root / 'query_memory.json'
        if qm_path.exists():
            raw = json.loads(qm_path.read_text('utf-8'))
            entries = raw.get('entries', raw.get('queries', []))
            if isinstance(entries, list):
                from collections import Counter
                fp_counts = Counter(e.get('fingerprint', '') for e in entries if e.get('fingerprint'))
                gaps = [
                    {'query': next(
                        (e.get('text', e.get('query_text', ''))[:80]
                         for e in entries if e.get('fingerprint') == fp), fp),
                     'count': c}
                    for fp, c in fp_counts.most_common(5) if c >= 3
                ]
                abandons = [
                    e.get('text', e.get('query_text', ''))[:80]
                    for e in reversed(entries) if not e.get('submitted', True)
                ][:5]
                signals['query'] = {'persistent_gaps': gaps, 'recent_abandons': abandons}
    except Exception:
        pass
    try:
        hm_path = root / 'file_heat_map.json'
        if hm_path.exists():
            raw = json.loads(hm_path.read_text('utf-8'))
            modules = {k: v for k, v in raw.items() if isinstance(v, dict)} if isinstance(raw, dict) else {}
            complex_files = sorted(
                [{'module': n,
                  'avg_hes': round(v.get('total_hes', 0) / max(v.get('samples', 1), 1), 3),
                  'avg_wpm': round(v.get('total_wpm', 0) / max(v.get('samples', 1), 1), 1),
                  'miss_count': v.get('miss_count', 0),
                  'samples': v.get('samples', 0)}
                 for n, v in modules.items()],
                key=lambda x: x['avg_hes'], reverse=True)
            high_hes = [c for c in complex_files if c['avg_hes'] >= 0.45]
            miss_files = [{'module': c['module'],
                           'miss_rate': round(c['miss_count'] / max(c['samples'], 1), 2)}
                          for c in complex_files if c['miss_count'] > 0]
            signals['heat'] = {'complex_files': high_hes[:6], 'high_miss_files': miss_files[:4]}
    except Exception:
        pass
    return signals
