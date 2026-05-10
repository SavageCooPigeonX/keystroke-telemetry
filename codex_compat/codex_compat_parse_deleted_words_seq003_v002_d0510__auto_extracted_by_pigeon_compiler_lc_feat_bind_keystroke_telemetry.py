"""codex_compat_parse_deleted_words_seq003_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 003 | VER: v002 | 23 lines | ~221 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
from .codex_compat_words_seq002_v002_d0510__auto_extracted_by_pigeon_compiler_lc_feat_bind_keystroke_telemetry import _words
from typing import Any
import re

def _parse_deleted_words(deleted_words: list[Any] | None = None, deleted_text: str = "") -> list[str]:
    words: list[str] = []
    for item in deleted_words or []:
        if isinstance(item, dict):
            text = item.get("word") or item.get("text") or item.get("deleted") or item.get("value") or ""
        else:
            text = str(item)
        words.extend(_words(text))
    words.extend(_words(deleted_text))
    seen = set()
    unique = []
    for word in words:
        key = word.lower()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(word)
    return unique[:30]
