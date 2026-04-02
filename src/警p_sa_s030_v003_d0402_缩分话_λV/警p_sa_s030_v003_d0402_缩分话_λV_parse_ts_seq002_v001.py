"""警p_sa_s030_v003_d0402_缩分话_λV_parse_ts_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone, timedelta
import re

def _parse_ts(raw: str, fmt: str) -> datetime | None:
    try:
        return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
    except Exception:
        return None
