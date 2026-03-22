"""operator_stats_seq008_time_utils_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone, timedelta
import re

def _hour_to_slot(hour: int) -> str:
    for name, (lo, hi) in TIME_SLOTS.items():
        if lo <= hour < hi:
            return name
    return "night"


def _local_hour_now() -> int:
    """Current local hour (0–23), no pytz needed."""
    return datetime.now().hour
