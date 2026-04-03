"""u_pe_s024_v004_d0403_λP0_βoc_active_dossier_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import re

def _write_routing_signal(root: Path, dossiers: list[dict]):
    """Write active dossier selection so task-context + auto-index can slim."""
    signal = {'ts': datetime.now(timezone.utc).isoformat(), 'dossiers': [], 'confidence': 0.0}
    if dossiers:
        top = dossiers[0]
        signal['confidence'] = top['score']
        signal['focus_modules'] = [d['file'] for d in dossiers[:5]]
        signal['focus_bugs'] = list(set(b for d in dossiers[:5] for b in d['bugs']))
        signal['dossiers'] = dossiers[:5]
    try:
        (root / 'logs' / 'active_dossier.json').write_text(
            json.dumps(signal, indent=2, default=str), 'utf-8')
    except Exception:
        pass


def _active_bug_dossier(root: Path, query: str, open_files: list | None = None) -> str:
    """Score, route, and format bug dossiers for the enricher prompt."""
    scored = _score_bug_dossiers(root, query, open_files)
    _write_routing_signal(root, scored)
    if not scored: return ''
    entries = []
    for d in scored[:6]:
        bug_str = ','.join(d['bugs'])
        line = f"  • {d['file']} [{bug_str}] score={d['score']} recur={d['recur']}"
        if d['entity']: line += f" demon=\"{d['entity']}\""
        if d['last_mark']: line += f" last_mark={d['last_mark']}"
        if d['last_change']: line += f" last_change=\"{d['last_change']}\""
        entries.append(line)
    return 'ACTIVE BUG DOSSIER (scored by: query+editor+hot_modules+recurrence):\n' + '\n'.join(entries)
