"""git_plugin_edit_tracking_seq013_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 013 | VER: v001 | 45 lines | ~351 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from pathlib import Path
import json
import re

def _load_edit_whys(root: Path) -> dict[str, str]:
    """Load latest edit_why per file from edit_pairs.jsonl."""
    ep = root / 'logs' / 'edit_pairs.jsonl'
    whys: dict[str, str] = {}
    if not ep.exists():
        return whys
    try:
        for line in ep.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            f = d.get('file', '')
            w = d.get('edit_why', '')
            if f and w and w != 'None':
                # Truncate to 3 words
                words = w.split()[:3]
                whys[f] = ' '.join(words)
    except Exception:
        pass
    return whys


def _load_edit_authors(root: Path) -> dict[str, str]:
    """Load latest edit_author per file from edit_pairs.jsonl."""
    ep = root / 'logs' / 'edit_pairs.jsonl'
    authors: dict[str, str] = {}
    if not ep.exists():
        return authors
    try:
        for line in ep.read_text(encoding='utf-8').splitlines():
            if not line.strip():
                continue
            d = json.loads(line)
            f = d.get('file', '')
            a = d.get('edit_author', '')
            if f and a:
                authors[f] = a
    except Exception:
        pass
    return authors
