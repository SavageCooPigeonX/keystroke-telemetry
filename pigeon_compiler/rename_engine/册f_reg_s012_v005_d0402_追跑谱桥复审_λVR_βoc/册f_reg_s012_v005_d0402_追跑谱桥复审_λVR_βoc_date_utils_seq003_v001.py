"""册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_date_utils_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
import re

def _today() -> str:
    """Return MMDD string for today (UTC)."""
    return datetime.now(timezone.utc).strftime('%m%d')
