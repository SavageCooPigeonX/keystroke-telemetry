"""compliance_seq008_classify_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def _classify(lc: int) -> str:
    if lc <= MAX_LINES:
        return 'OK'
    if lc <= WARN_LINES:
        return 'OVER'
    if lc <= CRIT_LINES:
        return 'WARN'
    return 'CRITICAL'
