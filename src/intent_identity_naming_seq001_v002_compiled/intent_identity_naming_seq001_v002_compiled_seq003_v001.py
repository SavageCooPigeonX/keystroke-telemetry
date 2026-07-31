"""intent_identity_naming_seq001_v002_compiled_seq003_v001.py — Auto-extracted by Pigeon Compiler."""
from .intent_identity_naming_seq001_v002_compiled_seq006_v001 import INTENT_STEM_RE
from .intent_identity_naming_seq001_v002_compiled_seq006_v001 import LC_SEP
from .intent_identity_naming_seq001_v002_compiled_seq006_v001 import _now
from typing import Any
import re

def parse_intent_stem(stem: str) -> dict[str, Any] | None:
    match = INTENT_STEM_RE.match(stem)
    if not match:
        return None
    slug = match.group("slug") or ""
    desc, last_change = "", ""
    if slug:
        if LC_SEP in slug:
            desc, last_change = slug.split(LC_SEP, 1)
        else:
            desc = slug
    return {
        "name": match.group("name"),
        "identity_id": match.group("name"),
        "itid": match.group("itid"),
        "seq": 0,
        "ver": int(match.group("ver")),
        "date": match.group("date") or "",
        "desc": desc,
        "intent": last_change,
        "last_change": last_change,
        "compressed": False,
        "naming": "intent_itid",
    }


def next_eci(entry: dict[str, Any], event: str) -> int:
    chain = list(entry.get("event_chain") or [])
    eci = int(entry.get("eci") or len(chain)) + 1
    chain.append({
        "eci": eci,
        "event": event,
        "ts": _now(),
        "intent_key": entry.get("intent_key", ""),
        "last_change": entry.get("last_change", ""),
    })
    entry["event_chain"] = chain[-32:]
    entry["eci"] = eci
    return eci
