"""谱建f_mb_s007_v003_d0314_观重箱重拆_λD_build_hesitation_summary_seq026_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 026 | VER: v001 | 57 lines | ~497 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re

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
