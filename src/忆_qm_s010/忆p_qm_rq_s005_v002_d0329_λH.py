"""query_memory_seq010_record_query_seq005_v001.py — Auto-extracted by Pigeon Compiler."""

from datetime import datetime, timezone
from pathlib import Path
import json
import re

def record_query(root: Path, query_text: str, submitted: bool,
                 unsaid: dict | None = None) -> None:
    """Persist a query + optional unsaid analysis to query_memory.json."""
    store_path = root / QUERY_STORE
    try:
        store = json.loads(store_path.read_text('utf-8')) if store_path.exists() else {}
    except Exception:
        store = {}

    queries  = store.get('queries', [])
    abandons = store.get('abandoned_themes', [])

    if submitted and query_text.strip():
        fp = _fingerprint(query_text)
        queries.append({
            'ts':          datetime.now(timezone.utc).isoformat(),
            'text':        query_text[:120],
            'fingerprint': fp,
            'submitted':   submitted,
        })

    # Integrate unsaid output
    if unsaid:
        for draft in unsaid.get('abandoned_drafts', []):
            if draft.get('text', '').strip():
                abandons.append({
                    'ts':    datetime.now(timezone.utc).isoformat(),
                    'text':  draft['text'][:120],
                    'state': draft.get('cognitive_state', 'unknown'),
                })
        for pivot in unsaid.get('topic_pivots', []):
            abandons.append({
                'ts':    datetime.now(timezone.utc).isoformat(),
                'text':  f"pivot: '{pivot.get('from_topic','?')}' → '{pivot.get('to_topic','?')}'",
                'state': 'pivot',
            })

    store['queries']           = queries[-MAX_ENTRIES:]
    store['abandoned_themes']  = abandons[-MAX_ENTRIES:]
    store_path.write_text(json.dumps(store, indent=2), encoding='utf-8')
