"""Registry + rename identity bridge — seq pairing, aliases, MD anchors."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v002 | 411 lines | ~3,500 tokens
# DESC:   seq_pairing_aliases_md_anchors
# INTENT: feat_add_intent_identity
# LAST:   2026-06-05 @ 912f0b2
# SESSIONS: 1
# ──────────────────────────────────────────────
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from src._resolve import src_import

SCHEMA = "registry_identity_bridge/v1"
ALIAS_SCHEMA = "file_identity_aliases/v1"
PAIRING_AUDIT = "logs/registry_pairing_audit_latest.json"
ALIASES_JSON = "logs/file_identity_aliases.json"
SKIP_REGISTRY_PREFIXES = ("build/", "tests/generated/", "rollback_logs/")
SKIP_REGISTRY_ROOT_SCRIPTS = True


def patch_registry(root: Path, *, write: bool = True, rebuild: bool = False) -> dict[str, Any]:
    """Bootstrap or reconcile pigeon_registry.json against disk."""
    root = Path(root)
    from pigeon_compiler.rename_engine import (
        build_registry_from_scan,
        load_registry,
        parse_pigeon_stem,
        save_registry,
    )
    from pigeon_compiler.rename_engine.扫p_sc_s001_v004_d0315_踪稿析_λν import scan_project

    catalog = scan_project(root)
    catalog["files"] = [
        f for f in catalog.get("files", [])
        if _include_in_registry(f.get("path", ""))
    ]
    scanned = build_registry_from_scan(root, catalog)
    scanned = {path: entry for path, entry in scanned.items() if _include_in_registry(path)}
    registry = load_registry(root)
    action = "loaded"

    if not registry or rebuild:
        registry = _enrich_entries(root, scanned)
        action = "bootstrapped"
    else:
        registry = _reconcile_registry(root, registry, scanned)
        action = "reconciled"

    audit = audit_registry_pairing(root, registry)
    result = {
        "schema": SCHEMA,
        "ts": _now(),
        "action": action,
        "entry_count": len(registry),
        "pairing_audit": audit,
        "paths": {"registry": "pigeon_registry.json", "aliases": ALIASES_JSON},
    }
    unified = unify_registry_intent_identity(root, registry, write=False)
    registry = unified.get("registry") or registry
    result["unified"] = {
        "enriched_count": unified.get("enriched_count", 0),
        "with_itid": unified.get("with_itid", 0),
        "with_parent": unified.get("with_parent", 0),
    }
    if write:
        save_registry(root, registry)
        _write_json(root / PAIRING_AUDIT, audit)
        _ensure_alias_store(root)
    return result


def unify_registry_intent_identity(
    root: Path,
    registry: dict[str, Any] | None = None,
    *,
    write: bool = True,
) -> dict[str, Any]:
    """Enrich every registry row with ITID/LH/ECI without disk rename."""
    root = Path(root)
    from pigeon_compiler.rename_engine import load_registry, save_registry

    registry = dict(registry if registry is not None else load_registry(root))
    enriched = 0
    with_itid = 0
    with_parent = 0
    for path, entry in list(registry.items()):
        row = dict(entry)
        _enrich_entry(root, path, row)
        if row.get("itid"):
            with_itid += 1
        if row.get("parent_lineage"):
            with_parent += 1
        registry[path] = row
        enriched += 1
        _merge_alias_identity(root, path, row, write=False)
    data = _load_aliases(root)
    _write_json(root / ALIASES_JSON, data) if write else None
    result = {
        "schema": "registry_unify_intent/v1",
        "ts": _now(),
        "enriched_count": enriched,
        "with_itid": with_itid,
        "with_parent": with_parent,
        "registry": registry,
    }
    if write:
        save_registry(root, registry)
        _write_json(root / "logs/registry_unify_intent_latest.json", result)
    return result


def _merge_alias_identity(root: Path, path: str, entry: dict[str, Any], *, write: bool) -> None:
    data = _load_aliases(root)
    aliases = data.setdefault("aliases", {})
    lh = str(entry.get("lh") or "")
    anchor = str(entry.get("identity_anchor") or "")
    record = {
        "current_file": path,
        "current_files": [path],
        "identity_id": entry.get("identity_id"),
        "itid": entry.get("itid"),
        "lh": lh,
        "intent_key": entry.get("intent_key", ""),
        "last_change": entry.get("last_change", ""),
        "parent_lineage": entry.get("parent_lineage") or {},
        "eci": entry.get("eci"),
    }
    for key in {path, anchor, lh, f"{entry.get('identity_id')}_lh_{lh}"}:
        if key:
            aliases[key] = dict(record)
    if write:
        _write_json(root / ALIASES_JSON, data)


def audit_registry_pairing(root: Path, registry: dict[str, Any] | None = None) -> dict[str, Any]:
    """Validate (name, seq) pairing between registry, disk, and session logs."""
    root = Path(root)
    from pigeon_compiler.rename_engine import load_registry, parse_pigeon_stem

    registry = registry if registry is not None else load_registry(root)
    mismatches: list[dict[str, Any]] = []
    orphans: list[str] = []
    matched = 0

    for path, entry in registry.items():
        stem = Path(path).stem
        parsed = parse_pigeon_stem(stem)
        if not parsed:
            orphans.append(path)
            continue
        name = str(entry.get("name") or "")
        seq = int(entry.get("seq") or 0)
        if parsed.get("seq") != seq or parsed.get("name") != name:
            mismatches.append({
                "path": path,
                "registry_name": name,
                "registry_seq": seq,
                "parsed_name": parsed.get("name"),
                "parsed_seq": parsed.get("seq"),
            })
        elif not (root / path).exists():
            mismatches.append({"path": path, "issue": "missing_on_disk"})
        else:
            matched += 1
        if not _include_in_registry(path):
            continue

    return {
        "schema": "registry_pairing_audit/v1",
        "ts": _now(),
        "matched": matched,
        "mismatch_count": len(mismatches),
        "orphan_count": len(orphans),
        "healthy": len(mismatches) == 0 and len(orphans) == 0,
        "mismatches": mismatches[:40],
        "orphans": orphans[:20],
    }


def merge_rename_alias(
    root: Path,
    old_path: str,
    new_path: str,
    entry: dict[str, Any],
    *,
    write: bool = True,
) -> dict[str, Any]:
    """Record old_path → new_path under stable ITID/LH identity."""
    root = Path(root)
    old_path = _norm(old_path)
    new_path = _norm(new_path)
    parent_lineage = {
        "lh": entry.get("lh", ""),
        "identity_id": entry.get("identity_id") or entry.get("name", ""),
        "itid": entry.get("itid", ""),
        "path": old_path,
        "intent_key": entry.get("intent_key", ""),
        "extraction": "version_bump_rename",
    }
    entry = dict(entry)
    entry["parent_lineage"] = parent_lineage
    record = {
        "current_file": new_path,
        "current_files": [new_path],
        "identity_id": entry.get("identity_id") or entry.get("name", ""),
        "itid": entry.get("itid", ""),
        "lh": entry.get("lh", ""),
        "eci": entry.get("eci"),
        "identity_anchor": entry.get("identity_anchor", ""),
        "intent_key": entry.get("intent_key", ""),
        "last_change": entry.get("last_change", ""),
        "parent_lineage": parent_lineage,
        "renamed_from": old_path,
        "renamed_at": _now(),
        "ver": entry.get("ver"),
        "desc": entry.get("desc", ""),
        "intent": entry.get("intent", ""),
    }
    data = _load_aliases(root)
    aliases = data.setdefault("aliases", {})
    keys = {
        old_path,
        new_path,
        entry.get("identity_anchor", ""),
        entry.get("lh", ""),
        f"{entry.get('identity_id')}_lh_{entry.get('lh')}",
    }
    for key in keys:
        if key:
            aliases[key] = dict(record)
    data["aliases"] = aliases
    data["last_rename"] = {"old": old_path, "new": new_path, "ts": _now(), "parent_lh": parent_lineage.get("lh")}
    if write:
        _write_json(root / ALIASES_JSON, data)
    return record


def prefer_legacy_filename(
    entry: dict[str, Any],
    *,
    date: str,
    desc: str,
    intent: str,
) -> str | None:
    """Build legacy semantic filename when enabled and name is readable."""
    if os.environ.get("PIGEON_PREFER_LEGACY_NAMES", "1").lower() in {"0", "false", "no"}:
        return None
    name = str(entry.get("semantic_name") or entry.get("name") or "").strip()
    if not name or _looks_compressed_name(name):
        return None
    from pigeon_compiler.rename_engine import build_pigeon_filename

    return build_pigeon_filename(
        name,
        int(entry.get("seq") or 0),
        int(entry.get("ver") or 1),
        date or str(entry.get("date") or ""),
        desc or str(entry.get("desc") or ""),
        intent or str(entry.get("intent") or ""),
    )


def resolve_registry_path(root: Path, key: str) -> str:
    """Resolve remembered path or identity_key to current file path."""
    root = Path(root)
    normalized = _norm(key)
    aliases = _load_aliases(root).get("aliases") or {}
    hit = aliases.get(normalized) or aliases.get(normalized.lstrip("./"))
    if isinstance(hit, dict) and hit.get("current_file"):
        return str(hit["current_file"])
    from pigeon_compiler.rename_engine import load_registry

    registry = load_registry(root)
    if normalized in registry:
        return normalized
    for path, entry in registry.items():
        identity = f"{entry.get('name')}_seq{int(entry.get('seq') or 0):03d}"
        if identity == normalized:
            return path
    return normalized


def _reconcile_registry(
    root: Path,
    registry: dict[str, Any],
    scanned: dict[str, Any],
) -> dict[str, Any]:
    by_identity: dict[str, dict[str, Any]] = {}
    for entry in registry.values():
        key = _identity_key(entry)
        if key:
            by_identity[key] = dict(entry)

    merged: dict[str, Any] = {}
    for path, scan_entry in scanned.items():
        identity = _identity_key(scan_entry)
        existing = by_identity.get(identity)
        if existing:
            row = dict(existing)
            row["path"] = path
            row.setdefault("semantic_name", _semantic_name(scan_entry, path))
            merged[path] = row
        else:
            merged[path] = _enrich_entry(root, path, dict(scan_entry))
    return merged


def _enrich_entries(root: Path, entries: dict[str, Any]) -> dict[str, Any]:
    return {path: _enrich_entry(root, path, dict(entry)) for path, entry in entries.items()}


def _enrich_entry(root: Path, path: str, entry: dict[str, Any]) -> dict[str, Any]:
    from pigeon_compiler.rename_engine import parse_pigeon_stem
    enrich_registry_entry = src_import("intent_identity_naming_seq001", "enrich_registry_entry")

    parsed = parse_pigeon_stem(Path(path).stem) or {}
    entry.setdefault("compressed", parsed.get("compressed", False))
    entry.setdefault("semantic_name", _semantic_name({**entry, **parsed}, path))
    intent_key = _intent_key_for_file(root, path)
    enrich_registry_entry(
        entry,
        path=path,
        intent_key=intent_key,
        last_change=str(entry.get("last_change") or entry.get("intent") or ""),
        event="registry_patch",
    )
    return entry


def _semantic_name(entry: dict[str, Any], path: str) -> str:
    if not entry.get("compressed") and entry.get("name") and not _looks_compressed_name(str(entry["name"])):
        return str(entry["name"])
    desc = str(entry.get("desc") or "").strip()
    if desc and not _looks_compressed_name(desc):
        slug = re.sub(r"[^a-z0-9]+", "_", desc.lower()).strip("_")
        if slug and len(slug) >= 3:
            return slug[:48]
    stem = Path(path).stem
    tokens = [t for t in re.split(r"[_\W]+", stem) if t and not re.match(r"^(seq|v|s|d)?\d+$", t, re.I)]
    ascii_tokens = [t for t in tokens if re.match(r"^[a-zA-Z][a-zA-Z0-9]*$", t)]
    if len(ascii_tokens) >= 2:
        return "_".join(ascii_tokens[:4]).lower()
    return str(entry.get("name") or "module")


def _intent_key_for_file(root: Path, path: str) -> str:
    try:
        from src.file_intent_identity_seq001_v001 import load_file_intent_map

        entry = load_file_intent_map(root, path)
        return str(entry.get("primary_intent_key") or "")
    except Exception:
        return ""


def _identity_key(entry: dict[str, Any]) -> str:
    name = str(entry.get("name") or "")
    seq = int(entry.get("seq") or 0)
    if not name:
        return ""
    return f"{name}_seq{seq:03d}"


def _looks_compressed_name(name: str) -> bool:
    return bool(re.search(r"[^\x00-\x7f]", name)) or bool(re.match(r"^[a-z]{1,3}f_[a-z]{1,4}$", name))


def _ensure_alias_store(root: Path) -> None:
    path = root / ALIASES_JSON
    if path.exists():
        return
    _write_json(path, {"schema": ALIAS_SCHEMA, "aliases": {}, "sources": {}})


def _load_aliases(root: Path) -> dict[str, Any]:
    data = _load_json(root / ALIASES_JSON)
    if isinstance(data, dict) and data.get("schema") == ALIAS_SCHEMA:
        return data
    return {"schema": ALIAS_SCHEMA, "aliases": {}, "sources": {}}


def _norm(path: str) -> str:
    return str(path or "").replace("\\", "/").strip()


def _include_in_registry(path: str) -> bool:
    rel = _norm(path)
    if not rel.endswith(".py"):
        return False
    if any(rel.startswith(prefix) for prefix in SKIP_REGISTRY_PREFIXES):
        return False
    if SKIP_REGISTRY_ROOT_SCRIPTS and "/" not in rel and rel.startswith("_"):
        return False
    return True


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
