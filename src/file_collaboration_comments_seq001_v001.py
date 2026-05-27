"""Manifest-state comments for file collaboration audits."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

COMMENT_SCHEMA = "file_manifest_comment/v1"
STATE_SCHEMA = "file_manifest_collaboration_state/v1"


def manifest_state(
    intent: dict[str, Any],
    metrics: dict[str, Any],
    verdict: str,
    comments: list[dict[str, Any]],
    ts: str,
) -> dict[str, Any]:
    intent_key = intent.get("intent_key") or "root:observe:file_collaboration:read"
    top_files = _dedupe(comment.get("from_file", "") for comment in comments)[:12]
    room = {
        "room_id": "manifest-room-" + hashlib.sha256("|".join(top_files).encode("utf-8")).hexdigest()[:10],
        "intent_key": intent_key,
        "shared_goal": "files collaborate through manifest state before any rewrite asks for source authority",
        "files": top_files,
        "agreement": room_agreement(metrics),
        "open_objections": room_objections(metrics),
        "next_plan": "load this state before the next sim, let files comment on peer plans, then reward outcomes back into file_profiles",
        "comments": comments[:12],
    }
    return {
        "schema": STATE_SCHEMA,
        "ts": ts,
        "primary_goal": "interlinked_source_state_through_file_collaboration",
        "verdict": verdict,
        "routing_rule": "future sims should load this state before selecting context packs or asking DeepSeek for rewrites",
        "operator_read": "This is the file room: agreements, objections, plans, and comments are durable state, not email confetti.",
        "rooms": [room],
    }


def file_comments(
    packets: list[dict[str, Any]],
    graph: dict[str, Any],
    outcomes: list[dict[str, Any]],
    registry: dict[str, Any],
) -> list[dict[str, Any]]:
    outcome_by_file = _latest_outcome_by_file(outcomes)
    registry_by_file = {item.get("file"): item for item in registry.get("files", []) if isinstance(item, dict)}
    comments = []
    for packet in packets[:12]:
        rel = str(packet.get("file") or "")
        if not rel:
            continue
        peers = _packet_peers(packet, graph)
        validation = (packet.get("verification_packet") or {}).get("validation_plan") or []
        size = packet.get("size_pressure") or {}
        comment = {
            "schema": COMMENT_SCHEMA,
            "comment_id": "fmc-" + hashlib.sha256(f"{rel}|{packet.get('packet_id')}".encode("utf-8")).hexdigest()[:14],
            "from_file": rel,
            "to_files": peers[:8],
            "stance": "agree_with_manifest_state" if peers else "needs_peer_binding",
            "learned": _learned_summary(packet, outcome_by_file.get(rel)),
            "plan": _plan(packet, validation, size),
            "blockers": _blockers(packet, validation, size),
            "manifest_claim": _manifest_claim(rel, packet, registry_by_file.get(rel)),
            "quote": _file_quote(rel, peers, validation, size, outcome_by_file.get(rel)),
        }
        comments.append(comment)
    return comments


def room_agreement(metrics: dict[str, Any]) -> str:
    if metrics.get("peer_ready_ratio", 0) >= 0.65:
        return "most waking files have peers or backward targets, so collaboration can become the routing default"
    return "files can wake and remember, but too many still lack explicit peer agreements"


def room_objections(metrics: dict[str, Any]) -> list[str]:
    objections = []
    if metrics.get("validation_ready_ratio", 0) < 0.75:
        objections.append("validation gates are not loaded for enough files")
    if metrics.get("relation_types", 0) < 3:
        objections.append("relationship graph is too flat; needs agreement/conflict/owner edges")
    if metrics.get("council_age_hours", 999) > 18:
        objections.append("file council latest is stale compared with the sim")
    if metrics.get("overcap_split_jobs", 0):
        objections.append(f"{metrics.get('overcap_split_jobs')} over-cap files want split plans")
    return objections


def _packet_peers(packet: dict[str, Any], graph: dict[str, Any]) -> list[str]:
    rel = str(packet.get("file") or "")
    peers = [
        str(item.get("file") or "") for item in packet.get("context_veins") or []
        if isinstance(item, dict)
    ]
    peers.extend(
        str(item.get("file") or "") for item in packet.get("backward_learning_targets") or []
        if isinstance(item, dict)
    )
    for edge in graph.get("edges") or []:
        if edge.get("from") == rel:
            peers.append(str(edge.get("to") or ""))
        if edge.get("to") == rel:
            peers.append(str(edge.get("from") or ""))
    return _dedupe(item for item in peers if item and item != rel)


def _learned_summary(packet: dict[str, Any], outcome: dict[str, Any] | None) -> str:
    knowledge = packet.get("accumulated_knowledge") or {}
    memory = knowledge.get("mail_memory") if isinstance(knowledge.get("mail_memory"), dict) else {}
    parts = [str(memory.get("summary") or "no mail memory yet")]
    parts.append(f"{knowledge.get('history_events', 0)} history event(s)")
    if outcome:
        parts.append(f"last outcome {outcome.get('outcome')} reward {outcome.get('reward')}")
    return "; ".join(parts)


def _plan(packet: dict[str, Any], validation: list[str], size: dict[str, Any]) -> str:
    if (packet.get("split_plan_request") or {}).get("needed"):
        return "draft a split plan only, keep facade stable, and demand peer context before source write"
    if validation:
        return "stay in learning mode, load peers, then allow a bounded rewrite only after validation passes"
    if size.get("needs_split_plan"):
        return "first map tests or compile gates; this file is too large to renovate by vibes"
    return "record manifest comment, wait for a stronger intent match, and do not spend context without a peer reason"


def _blockers(packet: dict[str, Any], validation: list[str], size: dict[str, Any]) -> list[str]:
    blockers = []
    if not validation:
        blockers.append("missing validation gate")
    if not packet.get("context_veins") and not packet.get("backward_learning_targets"):
        blockers.append("no explicit peer agreement yet")
    if size.get("state") in {"warn", "critical"}:
        blockers.append(f"over cap: {size.get('line_count')} lines")
    if (packet.get("overwrite_readiness") or {}).get("allowed") is False:
        blockers.append("overwrite blocked until operator approval")
    return blockers[:6]


def _manifest_claim(rel: str, packet: dict[str, Any], registry: dict[str, Any] | None) -> str:
    profile = packet.get("responsibility_profile") or {}
    identity = registry or {}
    role = profile.get("declared_role") or "file responsibility not declared"
    arch_seq = identity.get("arch_seq") or "unsequenced"
    return f"{rel} claims {role}; architecture spine {arch_seq}"


def _file_quote(rel: str, peers: list[str], validation: list[str], size: dict[str, Any], outcome: dict[str, Any] | None) -> str:
    stem = Path(rel).name
    if outcome and "fail" in str(outcome.get("outcome", "")).lower():
        return f"{stem}: I remember the failed run; bring tests before anyone hands DeepSeek a paint roller."
    if size.get("state") == "critical":
        return f"{stem}: I am {size.get('line_count')} lines and still being asked to fit in a carry-on. Manifest my roommates."
    if peers:
        return f"{stem}: I agree with {Path(peers[0]).name}, professionally, which is annoying because the graph has receipts."
    if not validation:
        return f"{stem}: I woke up without a test witness again. Very spiritual, legally useless."
    return f"{stem}: I have a plan, a gate, and exactly zero interest in mystery surgery."


def _latest_outcome_by_file(outcomes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_file = {}
    for row in outcomes:
        rel = row.get("file")
        if rel:
            by_file[str(rel)] = row
    return by_file


def _dedupe(items: Any) -> list[str]:
    seen = set()
    out = []
    for item in items:
        text = str(item or "")
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out
