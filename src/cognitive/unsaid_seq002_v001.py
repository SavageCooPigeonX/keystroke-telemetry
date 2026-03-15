"""Unsaid Thoughts Analyzer — detects what operators meant but didn't say.

Reconstructs abandoned drafts, restructured text, and deleted content from
keystroke telemetry to build an "unsaid thoughts" profile per session.

Capabilities:
  1. Understand what operator was TRYING to ask (even if they rewrote it)
  2. Track topics they started exploring but abandoned
  3. Detect uncertainty signals (repeated rewrites of the same concept)
  4. Identify emotional subtext (typed anger/frustration, then deleted it)
  5. Build richer cognitive profile for agent enrichment

Zero LLM calls — pure keystroke reconstruction + heuristics.
"""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 218 lines | ~2,045 tokens
# DESC:   detects_what_operators_meant_but
# INTENT: (none)
# LAST:   2026-03-15 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import re
from collections import defaultdict


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


def _diff_deleted(before: str, after: str) -> str:
    """Find text that was in 'before' but removed in 'after'."""
    if after in before:
        idx = before.find(after)
        deleted_before = before[:idx]
        deleted_after = before[idx + len(after):]
        return (deleted_before + deleted_after).strip()
    if len(before) <= len(after):
        return ''
    common_start = 0
    for i in range(min(len(before), len(after))):
        if before[i] == after[i]:
            common_start = i + 1
        else:
            break
    return before[common_start:len(before) - max(0, len(after) - common_start)].strip()


def _classify_position(full_text: str, deleted: str) -> str:
    """Classify where in the message the deletion occurred."""
    pos = full_text.find(deleted)
    if pos < 0:
        return 'unknown'
    ratio = pos / max(len(full_text), 1)
    if ratio < 0.25:
        return 'beginning'
    elif ratio < 0.75:
        return 'middle'
    return 'end'


def _classify_deletion_intent(text: str) -> str:
    """Classify the cognitive intent behind a deletion."""
    if len(text) > 50:
        return 'full_restart'
    if re.search(r'\?$', text.strip()):
        return 'question_abandoned'
    if re.search(r'^(can you|could you|would you|please|help)', text.strip(), re.I):
        return 'request_abandoned'
    if re.search(r'^(i think|i feel|maybe|actually)', text.strip(), re.I):
        return 'thought_suppressed'
    return 'general_edit'


def _extract_topic(text: str) -> str:
    """Extract a rough topic label from text (first few meaningful words)."""
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    stopwords = {'the', 'and', 'for', 'that', 'this', 'with', 'from', 'are', 'was', 'you', 'can', 'how'}
    meaningful = [w for w in words if w not in stopwords][:4]
    return ' '.join(meaningful) if meaningful else text[:30].strip()
