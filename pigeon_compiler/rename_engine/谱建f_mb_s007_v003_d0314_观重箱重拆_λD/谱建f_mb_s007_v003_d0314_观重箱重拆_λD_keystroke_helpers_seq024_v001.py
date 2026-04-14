"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_keystroke_helpers_seq024_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 024 | VER: v001 | 96 lines | ~854 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re

def _find_backspace_bursts(events: list[dict]) -> set[int]:
    """Return indices that are part of a backspace burst (3+ consecutive)."""
    burst_indices = set()
    run_start = None
    for i, ev in enumerate(events):
        if ev.get('event_type') in ('backspace', 'delete'):
            if run_start is None:
                run_start = i
        else:
            if run_start is not None and (i - run_start) >= BACKSPACE_BURST_MIN:
                for j in range(run_start, i):
                    burst_indices.add(j)
            run_start = None
    # Handle burst at end of trail
    if run_start is not None and (len(events) - run_start) >= BACKSPACE_BURST_MIN:
        for j in range(run_start, len(events)):
            burst_indices.add(j)
    return burst_indices


def _load_hesitation_map(root: Path) -> dict:
    """Load message_id → hesitation_score from all summary files."""
    hes = {}
    for d in LOG_DIRS:
        log_dir = root / d
        if not log_dir.is_dir():
            continue
        for sf in log_dir.glob('summary_*.json'):
            try:
                data = json.loads(sf.read_text(encoding='utf-8', errors='ignore'))
                for msg in data.get('messages', []):
                    mid = msg.get('message_id', '')
                    if mid:
                        hes[mid] = msg.get('hesitation_score', 0.0)
            except Exception:
                continue
    return hes


def _build_hesitation_summary(root: Path) -> list[str]:
    """Build recent-message hesitation table rows from newest summaries."""
    all_msgs = []
    for d in LOG_DIRS:
        log_dir = root / d
        if not log_dir.is_dir():
            continue
        for sf in sorted(log_dir.glob('summary_*.json'),
                         key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                data = json.loads(sf.read_text(encoding='utf-8', errors='ignore'))
                for msg in data.get('messages', []):
                    all_msgs.append(msg)
            except Exception:
                continue
            if len(all_msgs) >= 12:
                break
        if len(all_msgs) >= 12:
            break

    rows = []
    for msg in all_msgs[-12:]:
        mid = msg.get('message_id', '?')[:10]
        submitted = '✓' if msg.get('submitted') else '🗑'
        keys = msg.get('total_keystrokes', 0)
        dels = msg.get('total_deletions', 0)
        hes = msg.get('hesitation_score', 0.0)
        # Classify cognitive state inline
        state = _classify_msg_state(msg)
        rows.append(f'| `{mid}` | {submitted} | {keys} | {dels} | {hes:.3f} | {state} |')
    return rows


def _classify_msg_state(msg: dict) -> str:
    """Lightweight cognitive state classification for summary display."""
    keys = max(msg.get('total_keystrokes', 0), 1)
    dels = msg.get('total_deletions', 0)
    hes = msg.get('hesitation_score', 0.0)
    del_ratio = dels / keys
    if msg.get('deleted'):
        return 'abandoned'
    if hes > 0.6:
        return 'frustrated'
    if hes > 0.4:
        return 'hesitant'
    if del_ratio > 0.20:
        return 'restructuring'
    if hes < 0.15 and del_ratio < 0.05:
        return 'flow'
    if hes < 0.25:
        return 'focused'
    return 'neutral'
