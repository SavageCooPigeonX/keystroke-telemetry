"""engagement_hooks_helpers_seq001_v001.py — Auto-extracted by Pigeon Compiler."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v001 | 32 lines | ~206 tokens
# DESC:   auto_extracted_by_pigeon_compiler
# INTENT: (none)
# LAST:   2026-04-14 @ heal
# SESSIONS: 0
# ──────────────────────────────────────────────
from datetime import datetime, timezone
import json

def _json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text("utf-8", errors="ignore"))
    except Exception:
        return None


def _jsonl_tail(path, n=20):
    if not path.exists():
        return []
    ll = path.read_text("utf-8", errors="ignore").strip().splitlines()[-n:]
    out = []
    for l in ll:
        try:
            out.append(json.loads(l))
        except Exception:
            pass
    return out


def _hours_since(ts_str):
    try:
        t = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - t).total_seconds() / 3600
    except Exception:
        return 9999
