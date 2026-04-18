"""读f_fi_s016_v001_d0410_λFT_constants_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 17 lines | ~155 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
import json, os, re, hashlib, urllib.request, urllib.error

_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

_MODEL_FALLBACK = "gemini-flash-latest"  # reliable fallback alias

_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

_NM_FILE = "pigeon_brain/node_memory.json"

_MAX_SRC = 5000  # chars — keeps cost low, still enough signal


_BUG_SEV = {"oc": 0.8, "hi": 0.7, "hc": 0.6, "de": 0.4, "dd": 0.3, "qn": 0.2}

_BETA_RE = re.compile(r"_β(\w+?)(?:_|\.py$|$)")
