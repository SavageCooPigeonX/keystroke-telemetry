"""Intent identity naming — ITID + LH + ECI replaces meaningless seq."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LC_SEP = "_lc_"
INTENT_STEM_RE = re.compile(
    r"^(?P<name>.+)_it-(?P<itid>[a-z0-9][a-z0-9-]{1,48})_v(?P<ver>\d{3})"
    r"(?:_d(?P<date>\d{4}))?"
    r"(?:__(?P<slug>[a-z0-9_]+))?$"
)


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


def stamp_intent_touch(
    root: Path,
    file: str,
    *,
    intent_key: str,
    last_change: str,
    reason: str = "intent_touch",
    write: bool = True,
) -> dict[str, Any]:
    """Record ITID/LH/ECI + last_change for a touched file in registry."""
    root = Path(root)
    rel = str(file).replace("\\", "/").strip()
    from pigeon_compiler.rename_engine import load_registry, save_registry

    registry = load_registry(root)
    entry = dict(registry.get(rel) or {})
    if not entry:
        from pigeon_compiler.rename_engine import parse_pigeon_stem

        parsed = parse_pigeon_stem(Path(rel).stem) or parse_intent_stem(Path(rel).stem) or {}
        entry = {
            "path": rel,
            "name": parsed.get("name") or identity_id_from_path(rel),
            "seq": int(parsed.get("seq") or 0),
            "ver": int(parsed.get("ver") or 1),
            "date": parsed.get("date") or "",
            "desc": parsed.get("desc") or "",
            "intent": parsed.get("intent") or "",
            "history": [],
        }
    enrich_registry_entry(
        entry,
        path=rel,
        intent_key=intent_key,
        last_change=last_change or reason,
        event=reason,
    )
    entry["path"] = rel
    registry[rel] = entry
    result = {
        "schema": "intent_identity_touch/v1",
        "ts": _now(),
        "file": rel,
        "identity_id": entry.get("identity_id"),
        "itid": entry.get("itid"),
        "lh": entry.get("lh"),
        "eci": entry.get("eci"),
        "intent_key": entry.get("intent_key"),
        "last_change": entry.get("last_change"),
        "parent_lineage": entry.get("parent_lineage") or {},
    }
    if write:
        save_registry(root, registry)
        _append_jsonl(root / "logs/intent_identity_touches.jsonl", result)
    return result


def parent_lineage_from_compile(
    source_file: str,
    *,
    extraction: str = "auto_compile",
    parent_entry: dict[str, Any] | None = None,
) -> dict[str, Any]:
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
