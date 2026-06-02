"""Hush MAIF frontend interface packet.

This module treats Hush as the user-facing interface for myaifingerprint.com
information. It builds read-only entity simulation cards from fingerprint
records so a frontend can render audit, docs, copy, and file/entity views
without exposing closed-source repository contents.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "hush_maif_interface/v1"
LATEST = "logs/hush_maif_interface_latest.json"
MARKDOWN = "logs/hush_maif_interface.md"

MAIF_LABELS = {"maif_auditor", "linkrouter", "linkrouter_ai", "myaifingerprint"}
MAIF_TERMS = {
    "maif", "myaifingerprint", "hush", "entity", "entities", "audit",
    "auditor", "directory", "docs", "copy", "file", "spy", "shimmer",
    "fingerprint", "connected", "staged", "drift", "reputation", "sim",
}


def build_hush_maif_interface(root: Path, prompt: str = "", *, write: bool = True) -> dict[str, Any]:
    """Build the Hush packet a MAIF frontend can render for a user session."""
    root = Path(root)
    prompt = str(prompt or "")
    fingerprints = _load_maif_fingerprints(root)
    entities = _entity_sim(root, prompt, fingerprints)
    result = {
        "schema": SCHEMA,
        "ts": _now(),
        "surface": "myaifingerprint.com",
        "assistant": "Hush",
        "role": "maif_information_interface",
        "prompt": prompt,
        "frontend_intent": _frontend_intent(prompt),
        "first_run_notice": _first_run_notice(),
        "frontend_actions": _frontend_actions(prompt),
        "entity_sim": entities,
        "frontend_cards": _frontend_cards(entities),
        "operator_network_capability": _operator_network_capability(),
        "privacy": {
            "closed_repo_source": "not_exposed",
            "raw_keystrokes": "optional_consent_required",
            "network_egress": "disabled_by_default",
        },
        "paths": {"latest": LATEST, "markdown": MARKDOWN},
    }
    if write:
        _write_json(root / LATEST, result)
        (root / MARKDOWN).write_text(render_hush_maif_interface(result), encoding="utf-8")
    return result


def render_hush_maif_interface(packet: dict[str, Any]) -> str:
    lines = [
        "# Hush MAIF Interface",
        "",
        f"- surface: `{packet.get('surface')}`",
        f"- intent: `{packet.get('frontend_intent')}`",
        f"- role: `{packet.get('role')}`",
        "",
        "## First Run Notice",
        str((packet.get("first_run_notice") or {}).get("summary") or ""),
        "",
        "## Entity Sim",
    ]
    for entity in packet.get("entity_sim") or []:
        lines.append(
            f"- `{entity.get('entity_id')}` {entity.get('display_name')} "
            f"status `{entity.get('sim_state')}` confidence `{entity.get('confidence')}`"
        )
    lines.extend(["", "## Frontend Actions"])
    for action in packet.get("frontend_actions") or []:
        lines.append(f"- `{action.get('id')}`: {action.get('label')}")
    return "\n".join(lines) + "\n"


def _load_maif_fingerprints(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted((root / "logs").glob("repo_fingerprint_*.json")):
        data = _json(path)
        label = str(data.get("label") or path.stem.replace("repo_fingerprint_", ""))
        if label in MAIF_LABELS or set(_tokens(label)) & MAIF_TERMS:
            rows.append(data)
    if not rows:
        rows.append({
            "schema": "repo_fingerprint/v1",
            "label": "myaifingerprint",
            "privacy": "closed",
            "files_indexed": 0,
            "files": [],
        })
    return rows


def _entity_sim(root: Path, prompt: str, fingerprints: list[dict[str, Any]]) -> list[dict[str, Any]]:
    prompt_tokens = set(_tokens(prompt))
    entities: list[dict[str, Any]] = []
    for fp in fingerprints:
        label = str(fp.get("label") or "myaifingerprint")
        files = fp.get("files") if isinstance(fp.get("files"), list) else []
        for item in files[:12]:
            identity = str((item or {}).get("identity") or "")
            if not identity:
                continue
            entity_tokens = set(_tokens(identity.replace("_", " ")))
            matched = sorted((prompt_tokens & entity_tokens) | (prompt_tokens & MAIF_TERMS))
            entities.append({
                "schema": "hush_entity_sim/v1",
                "entity_id": identity,
                "display_name": _display_name(identity, label),
                "source": label,
                "privacy": fp.get("privacy", "closed"),
                "sim_state": _sim_state(prompt_tokens, identity),
                "confidence": round(min(1.0, 0.35 + len(matched) * 0.08), 3),
                "matched_terms": matched[:12],
                "summary": _entity_summary(identity, prompt_tokens),
                "allowed_actions": ["inspect_summary", "copy_entity_ref", "open_docs", "compare_drift"],
                "blocked_actions": ["raw_source_exfiltration", "autonomous_network_action"],
            })
    if entities:
        return sorted(entities, key=lambda row: (-row["confidence"], row["entity_id"]))[:8]
    fingerprint = _json(root / "logs" / "ai_fingerprint.json")
    return [{
        "schema": "hush_entity_sim/v1",
        "entity_id": "operator_ai_fingerprint",
        "display_name": "Operator AI Fingerprint",
        "source": "ai_fingerprint",
        "privacy": "local",
        "sim_state": "available" if fingerprint else "not_indexed",
        "confidence": 0.42 if fingerprint else 0.18,
        "matched_terms": sorted(prompt_tokens & MAIF_TERMS)[:12],
        "summary": "local fingerprint summary for the MAIF information interface",
        "allowed_actions": ["inspect_summary", "copy_entity_ref", "open_docs"],
        "blocked_actions": ["raw_source_exfiltration", "autonomous_network_action"],
    }]


def _frontend_intent(prompt: str) -> str:
    tokens = set(_tokens(prompt))
    if "sim" in tokens or "entity" in tokens or "entities" in tokens:
        return "entity_sim"
    if "audit" in tokens or "auditor" in tokens:
        return "audit_status"
    if "docs" in tokens:
        return "docs_lookup"
    if "copy" in tokens:
        return "copy_payload"
    if "file" in tokens:
        return "file_entity_lookup"
    return "maif_information"


def _frontend_actions(prompt: str) -> list[dict[str, str]]:
    requested = set(_tokens(prompt))
    actions = [
        ("spy", "Inspect signal summary"),
        ("docs", "Open docs for selected entity"),
        ("copy", "Copy selected entity reference"),
        ("file", "Show entity file/fingerprint card"),
        ("audit", "Show audit status"),
    ]
    rows = [{"id": key, "label": label} for key, label in actions]
    return sorted(rows, key=lambda row: (row["id"] not in requested, row["id"]))


def _first_run_notice() -> dict[str, Any]:
    return {
        "schema": "hush_first_run_notice/v1",
        "required": True,
        "summary": (
            "Hush can optionally use typing cadence, deletions, drafts, and entity "
            "interaction signals to personalize MAIF information. Monitoring is opt-in."
        ),
        "choices": ["enable_optional_signals", "continue_without_monitoring", "learn_more"],
    }


def _operator_network_capability() -> dict[str, Any]:
    return {
        "schema": "hush_operator_network_capability/v1",
        "status": "read_only_entity_sim",
        "intent_probes": "local_receipts_only",
        "proactive_actions": "suggest_only",
        "requires": [
            "first_run_terms_acceptance",
            "explicit_operator_ack",
            "entity_scope_lock",
            "network_egress_flag",
        ],
    }


def _frontend_cards(entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "schema": "hush_frontend_card/v1",
        "card_type": "entity",
        "title": entity["display_name"],
        "subtitle": entity["sim_state"],
        "entity_id": entity["entity_id"],
        "actions": entity["allowed_actions"],
        "privacy": entity["privacy"],
    } for entity in entities[:6]]


def _sim_state(tokens: set[str], identity: str) -> str:
    if "staged" in tokens or "marked" in tokens:
        return "marked_staged"
    if "connected" in tokens:
        return "connected"
    if "audit" in tokens or "auditor" in tokens:
        return "audit_ready"
    if "drift" in tokens:
        return "drift_watch"
    return "available"


def _entity_summary(identity: str, tokens: set[str]) -> str:
    name = _display_name(identity, "")
    if "audit" in tokens or "auditor" in tokens:
        return f"{name} is available for MAIF audit-status simulation."
    if "sim" in tokens:
        return f"{name} is represented as a read-only entity simulation."
    return f"{name} is available in the Hush information interface."


def _display_name(identity: str, label: str) -> str:
    raw = identity
    if label and raw.startswith(label + "_"):
        raw = raw[len(label) + 1:]
    words = [part for part in raw.split("_") if part]
    return " ".join(word[:1].upper() + word[1:] for word in words) or "MAIF Entity"


def _json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace")) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z][A-Za-z0-9_]{1,}", str(text or ""))]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
