"""u_pe_s024_v004_d0403_λP0_βoc_rework_attempts_seq004b_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import os
import re

def _rework_for_query(root: Path, query: str) -> list[dict]:
    """Find rework log entries related to the current query topic."""
    entries = _jsonl(root / 'rework_log.json', n=50)
    query_words = set(re.findall(r'\b\w{4,}\b', query.lower()))
    scored = []
    for e in entries:
        hint = (e.get('query_hint') or '').lower()
        overlap = len(query_words & set(re.findall(r'\b\w{4,}\b', hint)))
        if overlap >= 1:
            scored.append((overlap, e))
    scored.sort(key=lambda x: -x[0])
    return [e for _, e in scored[:MAX_REWORK_ENTRIES]]


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
