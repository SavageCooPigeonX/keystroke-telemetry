"""unsaid_seq002_orchestrator_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v002 | 151 lines | ~1,425 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: stage_hook_generated
# LAST:   2026-03-22 @ b48ee0a
# SESSIONS: 1
# ──────────────────────────────────────────────
import re

def extract_unsaid_thoughts(events: list, final_text: str = '') -> dict:
    """Analyze keystroke events to extract unsaid/deleted content.

    Args:
        events: List of keystroke event dicts from browser telemetry
        final_text: The text that was actually submitted

    Returns:
        {
            'abandoned_drafts': [{'text': str, 'deleted_at_ms': int, 'cognitive_state': str}],
            'deleted_fragments': [{'text': str, 'position': str, 'length': int}],
            'restructure_count': int,
            'topic_pivots': [{'from_topic': str, 'to_topic': str, 'pivot_at_ms': int}],
            'emotional_deletions': [{'text': str, 'emotion': str, 'deleted_at_ms': int}],
            'unsaid_summary': str,
            'confidence': float,
        }
    """
    result = {
        'abandoned_drafts': [],
        'deleted_fragments': [],
        'restructure_count': 0,
        'topic_pivots': [],
        'emotional_deletions': [],
        'unsaid_summary': '',
        'confidence': 0.0,
    }

    if not events:
        return result

    # Reconstruct buffer snapshots over time
    snapshots = []
    for evt in events:
        buf = evt.get('buffer', evt.get('buffer_snapshot', ''))
        ts = evt.get('timestamp_ms', 0)
        evt_type = evt.get('event_type', '')
        if buf is not None:
            snapshots.append({
                'text': str(buf),
                'ts': ts,
                'type': evt_type,
                'key': evt.get('key', ''),
            })

    if not snapshots:
        return result

    # Track text that appeared then disappeared
    max_buffer = ''
    deleted_fragments = []

    for snap in snapshots:
        current = snap['text']
        if len(current) > len(max_buffer):
            max_buffer = current
        elif len(current) < len(max_buffer) - 3:
            deleted = _diff_deleted(max_buffer, current)
            if deleted and len(deleted.strip()) >= 3:
                deleted_fragments.append({
                    'text': deleted.strip()[:200],
                    'position': _classify_position(max_buffer, deleted),
                    'length': len(deleted),
                    'deleted_at_ms': snap['ts'],
                })
            max_buffer = current

    result['deleted_fragments'] = deleted_fragments

    # Detect abandoned drafts
    for frag in deleted_fragments:
        if frag['length'] > 20:
            result['abandoned_drafts'].append({
                'text': frag['text'],
                'deleted_at_ms': frag['deleted_at_ms'],
                'cognitive_state': _classify_deletion_intent(frag['text']),
            })

    # Count restructures
    delete_runs = 0
    in_delete = False
    for snap in snapshots:
        if snap['type'] in ('delete', 'backspace'):
            if not in_delete:
                delete_runs += 1
                in_delete = True
        elif snap['type'] == 'insert':
            in_delete = False
    result['restructure_count'] = max(0, delete_runs - 1)

    # Detect topic pivots
    if len(deleted_fragments) >= 1 and final_text:
        for frag in deleted_fragments:
            if frag['length'] > 15:
                deleted_words = set(frag['text'].lower().split())
                final_words = set(final_text.lower().split())
                overlap = len(deleted_words & final_words) / max(len(deleted_words), 1)
                if overlap < 0.3:
                    result['topic_pivots'].append({
                        'from_topic': _extract_topic(frag['text']),
                        'to_topic': _extract_topic(final_text),
                        'pivot_at_ms': frag['deleted_at_ms'],
                    })

    # Detect emotional deletions
    _EMOTIONAL_PATTERNS = [
        (r'\b(fuck|shit|damn|wtf|angry|frustrated|hate|stupid|idiot|ugh)\b', 'frustration'),
        (r'\b(sorry|apologize|my fault|i messed up|my bad)\b', 'self_blame'),
        (r'\b(love|thank|grateful|amazing|awesome|incredible)\b', 'positive'),
        (r'\b(confused|lost|don\'?t understand|what|huh|help)\b', 'confusion'),
        (r'\b(worried|scared|anxious|nervous|afraid)\b', 'anxiety'),
        (r'\!{2,}|\?{3,}|\.{4,}', 'emphasis'),
    ]
    for frag in deleted_fragments:
        for pattern, emotion in _EMOTIONAL_PATTERNS:
            if re.search(pattern, frag['text'], re.IGNORECASE):
                result['emotional_deletions'].append({
                    'text': frag['text'][:100],
                    'emotion': emotion,
                    'deleted_at_ms': frag['deleted_at_ms'],
                })
                break

    # Build summary
    parts = []
    if result['abandoned_drafts']:
        parts.append(f"{len(result['abandoned_drafts'])} abandoned draft(s)")
    if result['topic_pivots']:
        pivots = '; '.join(
            f"'{p['from_topic'][:30]}' -> '{p['to_topic'][:30]}'"
            for p in result['topic_pivots'][:3]
        )
        parts.append(f"topic pivot(s): {pivots}")
    if result['emotional_deletions']:
        emotions = ', '.join(set(d['emotion'] for d in result['emotional_deletions']))
        parts.append(f"deleted emotional content ({emotions})")
    if result['restructure_count'] > 2:
        parts.append(f"{result['restructure_count']} restructures (heavy editing)")

    result['unsaid_summary'] = '; '.join(parts) if parts else ''
    result['confidence'] = min(1.0, (
        len(result['abandoned_drafts']) * 0.3 +
        len(result['deleted_fragments']) * 0.1 +
        len(result['topic_pivots']) * 0.2 +
        len(result['emotional_deletions']) * 0.2
    ))

    return result
