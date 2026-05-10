"""codex_compat_parse_iso_ts_seq051_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from typing import Any
import re

def _parse_iso_ts(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
