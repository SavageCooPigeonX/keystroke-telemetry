"""u_psg_s026_v001_logger_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v001 | 57 lines | ~498 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

def log_raw_signal(
    root: Path,
    msg: str,
    files_open: list[str],
    session_n: int,
    signals: dict[str, Any],
    deleted_words: list[str],
    rewrites: list[dict],
    composition_binding: dict[str, Any],
) -> dict[str, Any]:
    """Write one raw signal entry. Every field is measured, not interpreted.

    Returns the raw entry dict.
    """
    now = datetime.now(timezone.utc)

    entry: dict[str, Any] = {
        # ── identity ──
        'ts': now.isoformat(),
        'session_n': session_n,
        'msg': msg,
        'msg_len': len(msg),
        'files_open': files_open,
        # ── measured typing signals ──
        'signals': {
            'wpm': signals.get('wpm', 0),
            'chars_per_sec': signals.get('chars_per_sec', 0),
            'deletion_ratio': signals.get('deletion_ratio', 0),
            'hesitation_count': signals.get('hesitation_count', 0),
            'rewrite_count': signals.get('rewrite_count', 0),
            'typo_corrections': signals.get('typo_corrections', 0),
            'intentional_deletions': signals.get('intentional_deletions', 0),
            'total_keystrokes': signals.get('total_keystrokes', 0),
            'duration_ms': signals.get('duration_ms', 0),
        },
        # ── measured deletion content ──
        'deleted_words': deleted_words,
        'rewrites': rewrites,
        # ── composition binding (measured: which keystroke stream matched) ──
        'composition_binding': composition_binding,
        # ── provenance ──
        'provenance': 'measured',
    }

    # Append to raw signal log
    raw_path = root / RAW_JOURNAL_PATH
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    with open(raw_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    return entry
