"""intent_identity_naming_seq001_v002_compiled_seq004_v001.py — Auto-extracted by Pigeon Compiler."""
from .intent_identity_naming_seq001_v002_compiled_seq001_v001 import identity_id_from_path
from .intent_identity_naming_seq001_v002_compiled_seq001_v001 import intent_domain_for_path
from .intent_identity_naming_seq001_v002_compiled_seq001_v001 import itid_from_intent_key
from .intent_identity_naming_seq001_v002_compiled_seq001_v001 import lineage_hash
from .intent_identity_naming_seq001_v002_compiled_seq003_v001 import next_eci
from .intent_identity_naming_seq001_v002_compiled_seq006_v001 import _slug
from .intent_identity_naming_seq001_v002_compiled_seq006_v001 import _slug_lc
from typing import Any
import re

def enrich_registry_entry(
    entry: dict[str, Any],
    *,
    path: str,
    intent_key: str = "",
    last_change: str = "",
    parent_lineage: dict[str, Any] | None = None,
    event: str = "touch",
) -> dict[str, Any]:
    """Attach ITID/LH/ECI and last-change metadata to a registry row."""
    identity_id = str(entry.get("identity_id") or entry.get("name") or identity_id_from_path(path))
    domain = str(entry.get("intent_domain") or intent_domain_for_path(path))
    existing_key = str(entry.get("intent_key") or "")
    intent_key = str(intent_key or existing_key)
    existing_itid = str(entry.get("itid") or "")
    if intent_key:
        itid = itid_from_intent_key(intent_key)
    elif existing_itid and existing_itid != "unknown-intent":
        itid = existing_itid
    else:
        itid = _slug(identity_id) or "unknown-intent"
    parent = parent_lineage or entry.get("parent_lineage") or {}
    parent_lh = str(parent.get("lh") or "")
    entry["identity_id"] = identity_id
    entry["intent_domain"] = domain
    entry["itid"] = itid
    if intent_key:
        entry["intent_key"] = intent_key
    existing_lc = str(entry.get("last_change") or "")
    if last_change and last_change not in {"registered", "intent_touch", "registry_patch"}:
        entry["last_change"] = _slug_lc(last_change)[:48]
    elif existing_lc and existing_lc not in {"registered"}:
        entry["last_change"] = existing_lc
    entry["lh"] = lineage_hash(identity_id, domain, parent_lh)
    entry["parent_lineage"] = parent if parent else entry.get("parent_lineage") or {}
    if parent_lineage:
        entry["compiler_generation"] = int(parent_lineage.get("compiler_generation") or entry.get("compiler_generation") or 0) + 1
    next_eci(entry, event)
    entry["identity_anchor"] = f"{identity_id}_it-{itid}"
    return entry
