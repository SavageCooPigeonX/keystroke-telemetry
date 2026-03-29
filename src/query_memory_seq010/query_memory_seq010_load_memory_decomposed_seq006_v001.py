"""query_memory_seq010_load_memory_decomposed_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from collections import Counter
from pathlib import Path
import json
import re

def load_query_memory(root: Path) -> dict:
    """Load and aggregate query memory → summary for coaching prompt."""
    store_path = root / QUERY_STORE
    if not store_path.exists():
        return {}
    try:
        store = json.loads(store_path.read_text('utf-8'))
    except Exception:
        return {}

    queries  = store.get('queries', [])
    abandons = store.get('abandoned_themes', [])

    # Find recurring fingerprints
    fps = [q['fingerprint'] for q in queries if q.get('fingerprint')]
    counts = Counter(fps)
    persistent_gaps = [
        {'query': next((q['text'] for q in queries if q['fingerprint'] == fp), fp),
         'count': cnt}
        for fp, cnt in counts.most_common(5)
        if cnt >= RECUR_THRESH
    ]

    # Recent abandoned themes (last 10)
    recent_abandons = [a['text'] for a in abandons[-10:]]

    # Unsaid emotion distribution
    emotion_pattern = re.compile(r"pivot:|→")
    pivots = [a for a in abandons if emotion_pattern.search(a.get('text', ''))]

    return {
        'total_queries':     len(queries),
        'unique_topics':     len(counts),
        'persistent_gaps':   persistent_gaps,   # recurring = AI kept failing here
        'recent_abandons':   recent_abandons,    # what they started but didn't send
        'topic_pivot_count': len(pivots),
    }
