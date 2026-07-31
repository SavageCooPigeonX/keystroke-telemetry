"""Parse semantic intent-identity filenames through the rename-engine API."""

from __future__ import annotations

import re


INTENT_STEM_RE = re.compile(
    r"^(?P<name>.+)_it-(?P<itid>[a-z0-9][a-z0-9-]{1,48})_v(?P<ver>\d{3})"
    r"(?:_d(?P<date>\d{4}))?(?:__(?P<slug>[a-z0-9_]+))?$"
)


def parse_intent_pigeon_stem(stem: str) -> dict | None:
    """Return rename-engine fields for an ITID-format filename stem."""
    match = INTENT_STEM_RE.match(stem)
    if not match:
        return None
    slug = match.group("slug") or ""
    desc, intent = (slug.split("_lc_", 1) + [""])[:2] if "_lc_" in slug else (slug, "")
    return {
        "name": match.group("name"),
        "identity_id": match.group("name"),
        "itid": match.group("itid"),
        "seq": 0,
        "ver": int(match.group("ver")),
        "date": match.group("date") or "",
        "desc": desc,
        "intent": intent,
        "last_change": intent,
        "compressed": False,
        "naming": "intent_itid",
    }
