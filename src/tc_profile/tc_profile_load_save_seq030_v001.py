"""tc_profile_load_save_seq030_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 030 | VER: v001 | 33 lines | ~256 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
import json
import re
import time

from .tc_profile_constants_seq001_v001 import PROFILE_PATH

_profile_cache = None
_profile_ts = 0

def _empty_profile():
    return {
        'updated': None,
        'shards': {
            'sections': {},
            'intelligence': {'secrets': [], 'model': {}},
            'code_style': {},
        },
    }

def load_profile() -> dict:
    global _profile_cache, _profile_ts
    now = time.time()
    if _profile_cache and (now - _profile_ts) < 60:
        return _profile_cache
    if PROFILE_PATH.exists():
        try:
            _profile_cache = json.loads(PROFILE_PATH.read_text('utf-8', errors='ignore'))
            _profile_ts = now
            return _profile_cache
        except Exception:
            pass
    _profile_cache = _empty_profile()
    _profile_ts = now
    return _profile_cache


def save_profile(profile: dict):
    global _profile_cache, _profile_ts
    profile['updated'] = datetime.now(timezone.utc).isoformat()
    PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROFILE_PATH.write_text(
        json.dumps(profile, ensure_ascii=False, indent=1),
        encoding='utf-8',
    )
    _profile_cache = profile
    _profile_ts = time.time()
