"""读f_fi_s016_v001_d0410_λFT_priority_seq006_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 006 | VER: v001 | 7 lines | ~87 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json, os, re, hashlib, urllib.request, urllib.error

def _priority(entry: dict) -> float:
    bugs = [c for m in _BETA_RE.findall(entry.get("path", ""))
            for c in re.findall(r"[a-z]{2}", m)]
    return sum(_BUG_SEV.get(b, 0) for b in bugs)
