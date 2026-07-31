"""intent_identity_naming_seq001_v002_compiled_seq006_v001.py — Auto-extracted by Pigeon Compiler."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import re

def parent_lineage_from_compile(
    source_file: str,
    *,
    extraction: str = "auto_compile",
    parent_entry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from .intent_identity_naming_seq001_v002_compiled_seq001_v001 import (
        identity_id_from_path,
        intent_domain_for_path,
        itid_from_intent_key,
        lineage_hash,
    )

    parent_entry = parent_entry or {}
    identity_id = str(parent_entry.get("identity_id") or identity_id_from_path(source_file))
    domain = str(parent_entry.get("intent_domain") or intent_domain_for_path(source_file))
    lh = str(parent_entry.get("lh") or lineage_hash(identity_id, domain))
    return {
        "lh": lh,
        "identity_id": identity_id,
        "itid": parent_entry.get("itid") or itid_from_intent_key(str(parent_entry.get("intent_key") or "")),
        "path": source_file,
        "extraction": extraction,
        "intent_key": parent_entry.get("intent_key", ""),
        "compiler_generation": int(parent_entry.get("compiler_generation") or 0),
    }


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(text or "").lower()).strip("-")


def _slug_lc(text: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", str(text or "").lower()).strip("_")


def _slug_itid(text: str) -> str:
    slug = _slug(text).replace("-", "-")
    return slug[:48] or "unknown"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")

LC_SEP = "_lc_"

INTENT_STEM_RE = re.compile(
    r"^(?P<name>.+)_it-(?P<itid>[a-z0-9][a-z0-9-]{1,48})_v(?P<ver>\d{3})"
    r"(?:_d(?P<date>\d{4}))?"
    r"(?:__(?P<slug>[a-z0-9_]+))?$"
)
