"""u_pe_s024_v002_d0402_λC_context_fetchers_b2_seq007_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

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


def _recent_journal_context(root: Path, n: int = 6) -> list[dict]:
    """Pull last N journal entries as prompt trajectory — what operator was building toward."""
    entries = _jsonl(root / 'logs' / 'prompt_journal.jsonl', n=n)
    out = []
    for e in entries:
        deleted = [
            w.get('word', w) if isinstance(w, dict) else str(w)
            for w in (e.get('deleted_words') or [])
        ]
        rewrites = [
            f"{r.get('old','')} → {r.get('new','')}" if isinstance(r, dict) else str(r)
            for r in (e.get('rewrites') or [])
        ]
        out.append({
            'msg': (e.get('msg') or '')[:120],
            'intent': e.get('intent', 'unknown'),
            'state': e.get('state', 'unknown'),
            'deleted': deleted,
            'rewrites': rewrites,
        })
    return out
