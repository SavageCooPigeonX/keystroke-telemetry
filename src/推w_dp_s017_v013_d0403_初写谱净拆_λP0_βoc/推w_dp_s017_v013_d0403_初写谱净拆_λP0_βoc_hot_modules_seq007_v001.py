"""推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_hot_modules_seq007_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 007 | VER: v001 | 23 lines | ~236 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
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
