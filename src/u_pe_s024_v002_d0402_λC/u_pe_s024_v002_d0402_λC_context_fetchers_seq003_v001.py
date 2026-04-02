"""u_pe_s024_v002_d0402_λC_context_fetchers_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import json
import os
import re

def _hot_files(root: Path, top_n: int = 5) -> list[dict]:
    """Return top N files by hesitation score from file_heat_map."""
    raw = _jload(root / 'file_heat_map.json')
    if not raw or not isinstance(raw, dict): return []
    items = []
    for name, v in raw.items():
        if not isinstance(v, dict): continue
        hes = v.get('avg_hes', 0)
        touches = v.get('total', 0)
        if touches >= 2:
            items.append({'file': name, 'hes': round(hes, 3), 'touches': touches})
    return sorted(items, key=lambda x: x['hes'], reverse=True)[:top_n]


def _registry_touches(root: Path, query: str) -> list[dict]:
    """Find registry entries for modules mentioned in the query."""
    reg = _jload(root / 'pigeon_registry.json')
    if not reg: return []
    files = reg if isinstance(reg, list) else reg.get('files', [])
    query_lower = query.lower()
    hits = []
    for f in files:
        name = f.get('file', '') or f.get('desc', '')
        seq = f.get('seq', '')
        if any(part in query_lower for part in name.lower().split('_') if len(part) > 3):
            hits.append({
                'file': name,
                'ver': f.get('ver', '?'),
                'desc': f.get('desc', ''),
                'intent': f.get('intent', ''),
            })
    return hits[:4]


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
