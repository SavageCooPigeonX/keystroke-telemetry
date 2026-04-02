"""manifest_builder_seq007_keystroke_trail_decomposed_seq027_v001.py — Auto-extracted by Pigeon Compiler."""
from pathlib import Path
import ast
import json
import re

def _build_keystroke_trail(root: Path, now: str) -> str:
    """Build the OPERATOR KEYSTROKE TRAIL section for MASTER_MANIFEST.md.

    Reads the most recent event JSONL files across all log directories,
    extracts the last 50 keystrokes, and annotates them with:
      ⏸  pause  — gap > 2 s between keystrokes
      ⌫  burst  — 3+ consecutive backspaces
      🗑 discard — message was abandoned / deleted
      ✓  submit — message was submitted

    Also loads matching summary files for per-message hesitation scores.
    """
    # Collect all event files sorted by modification time (most recent last)
    event_files = []
    for d in LOG_DIRS:
        log_dir = root / d
        if log_dir.is_dir():
            for f in log_dir.glob('events_*.jsonl'):
                event_files.append(f)
    if not event_files:
        return ''
    event_files.sort(key=lambda p: p.stat().st_mtime)

    # Load events from the most recent files until we have >= TRAIL_LIMIT
    all_events = []
    for ef in reversed(event_files):
        try:
            lines = ef.read_text(encoding='utf-8', errors='ignore').strip().splitlines()
            events = [json.loads(ln) for ln in lines if ln.strip()]
            all_events = events + all_events
        except Exception:
            continue
        if len(all_events) >= TRAIL_LIMIT:
            break
    if not all_events:
        return ''

    # Take last TRAIL_LIMIT events
    trail = all_events[-TRAIL_LIMIT:]

    # Load summary files for hesitation lookup
    hes_map = _load_hesitation_map(root)

    # Build annotated trail
    lines = []
    lines.append('## OPERATOR KEYSTROKE TRAIL')
    lines.append('')
    lines.append(f'*Last {len(trail)} keystrokes | auto-synced by manifest_builder | {now}*')
    lines.append('')
    lines.append('> **How to read**: Each row is one keystroke event from the operator.')
    lines.append('> Markers flag cognitive signals: ⏸ = long pause (>2s), ')
    lines.append('> ⌫ = backspace burst (3+), ✓ = submitted, 🗑 = discarded.')
    lines.append('> Hesitation scores come from session summaries (0.0 = confident, 1.0 = max hesitation).')
    lines.append('')
    lines.append('| # | Key | Event | Δms | Buffer | Markers |')
    lines.append('|---|-----|-------|----:|--------|---------|')

    # Pre-compute backspace bursts
    burst_indices = _find_backspace_bursts(trail)

    for i, ev in enumerate(trail):
        markers = []
        delta = ev.get('delta_ms', 0)
        etype = ev.get('event_type', '')
        key = ev.get('key', '')
        buf = ev.get('buffer', '')
        msg_id = ev.get('message_id', '')

        # Pause marker
        if delta > PAUSE_THRESHOLD_MS:
            markers.append(f'⏸ {delta/1000:.1f}s')

        # Backspace burst marker
        if i in burst_indices:
            markers.append('⌫ burst')

        # Submit / discard markers (on submit/discard event types)
        if etype == 'submit':
            hes = hes_map.get(msg_id)
            tag = '✓ submit'
            if hes is not None:
                tag += f' (hes={hes:.3f})'
            markers.append(tag)
        elif etype == 'discard':
            hes = hes_map.get(msg_id)
            tag = '🗑 discard'
            if hes is not None:
                tag += f' (hes={hes:.3f})'
            markers.append(tag)

        # Truncate buffer for readability
        buf_display = buf if len(buf) <= 30 else buf[:27] + '...'
        # Escape pipe characters in buffer
        buf_display = buf_display.replace('|', '\\|')
        marker_str = ' '.join(markers)
        seq = i + 1
        lines.append(f'| {seq} | `{key}` | {etype} | {delta} | `{buf_display}` | {marker_str} |')

    lines.append('')

    # Append hesitation summary for recent messages
    hes_summary = _build_hesitation_summary(root)
    if hes_summary:
        lines.append('### Recent message hesitation scores')
        lines.append('')
        lines.append('| Message | Submitted | Keys | Dels | Hesitation | State |')
        lines.append('|---------|-----------|-----:|-----:|-----------:|-------|')
        lines.extend(hes_summary)
        lines.append('')

    return '\n'.join(lines)
