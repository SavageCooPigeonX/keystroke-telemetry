"""dynamic_prompt_seq017_metrics_analysis_b_seq005_v001.py — Auto-extracted by Pigeon Compiler."""
from collections import Counter
import json, re, subprocess

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
