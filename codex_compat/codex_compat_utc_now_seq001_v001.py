"""codex_compat_utc_now_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
import re

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
