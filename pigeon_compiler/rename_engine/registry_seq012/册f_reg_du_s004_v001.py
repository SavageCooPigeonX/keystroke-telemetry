"""registry_seq012_date_utils_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
import re

def _today() -> str:
    """Return MMDD string for today (UTC)."""
    return datetime.now(timezone.utc).strftime('%m%d')
