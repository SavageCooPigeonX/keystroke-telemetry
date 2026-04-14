"""推w_dp_s017_v013_d0403_初写谱净拆_λP0_βoc_other_metrics_seq008_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 008 | VER: v001 | 37 lines | ~397 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from collections import Counter
import json, re, subprocess

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
