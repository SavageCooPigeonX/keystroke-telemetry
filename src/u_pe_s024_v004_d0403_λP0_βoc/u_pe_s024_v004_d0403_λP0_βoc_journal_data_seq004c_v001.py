"""u_pe_s024_v004_d0403_λP0_βoc_journal_data_seq004c_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import re

def _deleted_words_from_journal(root: Path, n: int = 3) -> list[str]:
    """Pull deleted words from the last N journal entries."""
    entries = _jsonl(root / 'logs' / 'prompt_journal.jsonl', n=n)
    words = []
    for e in entries:
        for w in (e.get('deleted_words') or []):
            word = w.get('word', w) if isinstance(w, dict) else str(w)
            if word and len(word) > 2:
                words.append(word)
    return words[-MAX_DELETED_WORDS:]


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
