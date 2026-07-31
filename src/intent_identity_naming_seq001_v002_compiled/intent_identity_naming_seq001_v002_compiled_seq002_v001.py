"""intent_identity_naming_seq001_v002_compiled_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from .intent_identity_naming_seq001_v002_compiled_seq006_v001 import LC_SEP
from .intent_identity_naming_seq001_v002_compiled_seq006_v001 import _slug
from .intent_identity_naming_seq001_v002_compiled_seq006_v001 import _slug_itid
from .intent_identity_naming_seq001_v002_compiled_seq006_v001 import _slug_lc
import re

def build_intent_filename(
    identity_id: str,
    itid: str,
    ver: int,
    *,
    date: str = "",
    desc: str = "",
    last_change: str = "",
) -> str:
    """Build semantic intent filename (no seq digit)."""
    base = f"{_slug(identity_id)}_it-{_slug_itid(itid)}_v{int(ver):03d}"
    if date:
        base += f"_d{date}"
    desc = _slug_lc(desc)
    last_change = _slug_lc(last_change)
    if desc and last_change:
        base += f"__{desc}{LC_SEP}{last_change}"
    elif desc:
        base += f"__{desc}"
    elif last_change:
        base += f"__touch{LC_SEP}{last_change}"
    return base + ".py"
