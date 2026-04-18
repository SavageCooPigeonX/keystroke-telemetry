"""推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_metrics_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v001 | 59 lines | ~598 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import Counter
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


def _trajectory(root):
    raw = _json(root / 'logs' / 'copilot_prompt_mutations.json')
    if not raw: return {}
    snaps = raw.get('snapshots', [])
    if len(snaps) < 2: return {}
    first, last = snaps[0], snaps[-1]
    gained = [k for k, v in last.get('features', {}).items()
              if v and not first.get('features', {}).get(k)]
    return {'n': len(snaps), 'l0': first.get('lines', 0),
            'l1': last.get('lines', 0), 'feat': gained}


def _gaps(root):
    raw = _json(root / 'query_memory.json')
    if not raw: return []
    qs = raw.get('queries', raw if isinstance(raw, list) else [])
    fp = Counter(q.get('fingerprint', '') for q in qs
                 if q.get('fingerprint', '') not in ('', 'background')
                 and not q.get('fingerprint', '').startswith('bg'))
    return [{'q': f, 'n': n} for f, n in fp.most_common(4) if n >= 2]
