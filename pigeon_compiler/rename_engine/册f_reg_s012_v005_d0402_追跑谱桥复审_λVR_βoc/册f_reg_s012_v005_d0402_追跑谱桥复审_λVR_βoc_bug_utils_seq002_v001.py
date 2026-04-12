"""册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_bug_utils_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
import re

from .册f_reg_s012_v005_d0402_追跑谱桥复审_λVR_βoc_constants_seq001_v001 import BUG_KEY_ORDER

def bug_keys_from_marker(marker: str) -> list[str]:
    """Decode a compact bug marker string into 2-letter bug keys.

    'ochi' -> ['oc', 'hi']
    """
    marker = (marker or '').strip().lower()
    return [marker[i:i + 2] for i in range(0, len(marker), 2)
            if len(marker[i:i + 2]) == 2]


def bug_marker_from_keys(keys: list[str] | tuple[str, ...]) -> str:
    """Encode ordered bug keys into an identifier-safe filename marker.

    ['oc', 'hi'] -> 'ochi'
    """
    unique = {
        str(key).lower() for key in keys
        if isinstance(key, str) and len(str(key).strip()) == 2
    }
    ordered = [key for key in BUG_KEY_ORDER if key in unique]
    ordered.extend(sorted(key for key in unique if key not in BUG_KEY_ORDER))
    return ''.join(ordered)
