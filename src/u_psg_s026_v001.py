"""Raw prompt signal — measured truth only, no interpretation.

This is the ground-truth signal layer. Every field here comes from
direct measurement (keystroke timing, editor state, file system).
NO intent classification, NO cognitive state labels, NO LLM outputs.

Downstream modules can trust every field in prompt_signal_raw.jsonl
as measured reality — it will never contain hallucination or opinion.

The enriched prompt_journal.jsonl READS from this and ADDS interpretation.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RAW_JOURNAL_PATH = 'logs/prompt_signal_raw.jsonl'


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


def load_raw_signals(root: Path, after_line: int = 0) -> list[dict[str, Any]]:
    """Load raw signal entries, optionally after a specific line number."""
    p = root / RAW_JOURNAL_PATH
    if not p.exists():
        return []
    entries = []
    with open(p, encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            if i <= after_line or not line.strip():
                continue
            try:
                entries.append(json.loads(line))
            except Exception:
                pass
    return entries


def load_latest_raw(root: Path, n: int = 1) -> list[dict[str, Any]]:
    """Load the most recent N raw signal entries."""
    p = root / RAW_JOURNAL_PATH
    if not p.exists():
        return []
    try:
        lines = p.read_text(encoding='utf-8').strip().splitlines()
        result = []
        for line in lines[-n:]:
            if line.strip():
                result.append(json.loads(line))
        return result
    except Exception:
        return []
