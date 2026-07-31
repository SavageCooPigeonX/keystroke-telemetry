"""intent_identity_naming_seq001_v002_compiled_seq001_v001.py — Auto-extracted by Pigeon Compiler."""
from .intent_identity_naming_seq001_v002_compiled_seq003_v001 import parse_intent_stem
from .intent_identity_naming_seq001_v002_compiled_seq006_v001 import _slug
from pathlib import Path
import hashlib
import re

def itid_from_intent_key(intent_key: str) -> str:
    """verb-target slug from scope:verb:target:scale."""
    parts = str(intent_key or "").split(":")
    if len(parts) >= 4:
        verb = _slug(parts[1])
        target = _slug(parts[2])[:24]
        if verb and target:
            return f"{verb}-{target}"[:48]
    return _slug(intent_key)[:48] or "unknown-intent"


def lineage_hash(identity_id: str, intent_domain: str = "", parent_lh: str = "") -> str:
    """Stable 4-char address for a logical module lineage."""
    seed = "|".join([
        _slug(identity_id),
        _slug(intent_domain),
        parent_lh or "",
    ])
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:4]


def intent_domain_for_path(path: str) -> str:
    rel = str(path or "").replace("\\", "/").strip()
    if rel.startswith("src/") and rel.count("/") >= 2:
        return "/".join(rel.split("/")[:2])
    if "/" in rel:
        return str(Path(rel).parent).replace("\\", "/")
    return "root"


def identity_id_from_path(path: str) -> str:
    stem = Path(str(path or "")).stem
    parsed = parse_intent_stem(stem) or {}
    if parsed.get("name"):
        return str(parsed["name"])
    legacy = re.match(r"^(.+)_seq\d{3}_v\d{3}", stem)
    if legacy:
        return legacy.group(1)
    return _slug(stem) or "module"
