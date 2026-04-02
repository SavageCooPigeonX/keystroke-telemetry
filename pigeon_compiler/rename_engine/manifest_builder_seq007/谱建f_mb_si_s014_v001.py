"""manifest_builder_seq007_status_icon_seq014_v001.py — Auto-extracted by Pigeon Compiler."""
import re

def _status_icon(line_count: int) -> str:
    if line_count <= MAX_COMPLIANT:
        return '✅'
    elif line_count <= 300:
        return '⚠️ OVER'
    elif line_count <= 500:
        return '🟠 WARN'
    else:
        return '🔴 CRIT'
