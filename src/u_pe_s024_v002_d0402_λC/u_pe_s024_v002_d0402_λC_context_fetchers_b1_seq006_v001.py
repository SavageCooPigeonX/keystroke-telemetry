"""u_pe_s024_v002_d0402_λC_context_fetchers_b1_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import os
import re

def _recent_ai_attempts(root: Path, query: str) -> list[dict]:
    """Find the most recent AI responses relevant to this query topic."""
    entries = _jsonl(root / 'logs' / 'ai_responses.jsonl', n=30)
    query_words = set(re.findall(r'\b\w{4,}\b', query.lower()))
    scored = []
    for e in entries:
        prompt = (e.get('prompt') or '').lower()
        overlap = len(query_words & set(re.findall(r'\b\w{4,}\b', prompt)))
        if overlap >= 2:
            scored.append((overlap, e))
    scored.sort(key=lambda x: -x[0])
    hits = []
    for _, e in scored[:MAX_AI_RESPONSES]:
        hits.append({
            'prompt_preview': (e.get('prompt') or '')[:80],
            'response_preview': (e.get('response') or '')[:120],
            'ts': e.get('ts', ''),
        })
    return hits


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
