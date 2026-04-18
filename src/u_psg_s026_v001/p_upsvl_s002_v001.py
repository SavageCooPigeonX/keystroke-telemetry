"""u_psg_s026_v001_loaders_seq002_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 002 | VER: v001 | 36 lines | ~286 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
from typing import Any
import json

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
