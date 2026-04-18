"""unsaid_accumulator_seq001_v001.py — long-term unsaid thread history.

Persistently stores deleted thoughts, completed intents, and unsaid
threads. Builds a growing profile of operator thinking over time.
Usable for code, email drafts, docs — anything.

Usage:
    from src.unsaid_accumulator_seq001_v001_seq001_v001 import record, get_recent, get_summary
    record("the drift watch", "the drift watcher should track module renames")
    print(get_summary())
"""
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UNSAID_LOG = ROOT / 'logs' / 'unsaid_history.jsonl'


def record(fragment: str, completed_intent: str,
           deleted_words: list[str] | None = None,
           unsaid_threads: list[str] | None = None,
           context: str = 'code') -> dict:
    """Persist an unsaid thread entry. Returns the stored entry."""
    entry = {
        'ts': datetime.now(timezone.utc).isoformat(),
        'fragment': fragment[:500],
        'completed_intent': completed_intent[:500],
        'deleted_words': (deleted_words or [])[:20],
        'unsaid_threads': (unsaid_threads or [])[:10],
        'context': context,
    }
    UNSAID_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(UNSAID_LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    return entry


def get_recent(n: int = 10) -> list[dict]:
    """Last N unsaid entries."""
    if not UNSAID_LOG.exists():
        return []
    try:
        lines = UNSAID_LOG.read_text('utf-8', errors='ignore').strip().split('\n')
        return [json.loads(l) for l in lines[-n:] if l.strip()]
    except Exception:
        return []


def query(topic: str = '', limit: int = 20) -> list[dict]:
    """Search unsaid history by topic keyword."""
    if not UNSAID_LOG.exists():
        return []
    results = []
    topic_lower = topic.lower()
    try:
        for line in UNSAID_LOG.read_text('utf-8', errors='ignore').strip().split('\n'):
            if not line.strip():
                continue
            entry = json.loads(line)
            if not topic or topic_lower in entry.get('completed_intent', '').lower() \
                    or topic_lower in entry.get('fragment', '').lower() \
                    or any(topic_lower in t.lower() for t in entry.get('unsaid_threads', [])):
                results.append(entry)
            if len(results) >= limit:
                break
    except Exception:
        pass
    return results


def get_summary(max_threads: int = 10) -> str:
    """Compressed summary of recent unsaid threads for LLM context."""
    recent = get_recent(max_threads)
    if not recent:
        return ''
    parts = [f'Unsaid thread history ({len(recent)} recent):']
    for entry in recent:
        intent = entry.get('completed_intent', '')[:80]
        ctx = entry.get('context', 'code')
        parts.append(f'- [{ctx}] {intent}')
        deleted = entry.get('deleted_words', [])
        if deleted:
            parts.append(f'  deleted: {", ".join(deleted[:5])}')
    return '\n'.join(parts)
