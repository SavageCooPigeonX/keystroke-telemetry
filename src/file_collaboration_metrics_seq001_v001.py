"""Metrics for file-sim collaboration audits."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def collaboration_metrics(
    latest: dict[str, Any],
    graph: dict[str, Any],
    history: list[dict[str, Any]],
    outcomes: list[dict[str, Any]],
    council: dict[str, Any],
    logs: Path,
) -> dict[str, Any]:
    packets = [item for item in latest.get("learning_packets", []) if isinstance(item, dict)]
    edges = [item for item in graph.get("edges", []) if isinstance(item, dict)]
    relation_counts = Counter(str(edge.get("relation") or edge.get("type") or "unknown") for edge in edges)
    peer_ready = [
        packet for packet in packets
        if packet.get("context_veins") or packet.get("backward_learning_targets")
    ]
    validation_ready = [
        packet for packet in packets
        if (packet.get("verification_packet") or {}).get("validation_plan")
    ]
    history_edges = [
        len(((row.get("relationship_graph") or {}).get("edges") or []))
        for row in history
        if isinstance(row, dict) and row.get("relationship_graph")
    ]
    pass_count = sum(1 for row in outcomes if "pass" in str(row.get("outcome", "")).lower())
    fail_count = sum(1 for row in outcomes if "fail" in str(row.get("outcome", "")).lower())
    rewards = [float(row.get("reward") or 0.0) for row in outcomes if isinstance(row, dict)]
    return {
        "relationship_edges": len(edges),
        "relationship_nodes": len(graph.get("nodes") or []),
        "relation_counts": dict(relation_counts),
        "relation_types": len(relation_counts),
        "learning_packets": len(packets),
        "peer_ready_packets": len(peer_ready),
        "peer_ready_ratio": _ratio(len(peer_ready), len(packets)),
        "validation_ready_packets": len(validation_ready),
        "validation_ready_ratio": _ratio(len(validation_ready), len(packets)),
        "context_veins": sum(len(packet.get("context_veins") or []) for packet in packets),
        "backward_targets": sum(len(packet.get("backward_learning_targets") or []) for packet in packets),
        "outcomes_seen": len(outcomes),
        "outcome_pass_count": pass_count,
        "outcome_fail_count": fail_count,
        "outcome_pass_rate": _ratio(pass_count, pass_count + fail_count),
        "average_reward": round(sum(rewards) / max(1, len(rewards)), 3),
        "edge_history": history_edges[-12:],
        "edge_trend": edge_trend(history_edges),
        "latest_age_hours": age_hours(latest.get("ts")),
        "council_age_hours": file_age_hours(logs / "file_job_council_latest.json", council.get("ts")),
        "overcap_split_jobs": len(latest.get("overcap_split_jobs") or []),
        "interlink_jobs": len((latest.get("interlink_plan") or {}).get("near_term_jobs") or []),
    }


def collaboration_score(metrics: dict[str, Any]) -> float:
    edge_score = min(1.0, metrics.get("relationship_edges", 0) / 24.0)
    relation_score = min(1.0, metrics.get("relation_types", 0) / 4.0)
    packet_score = min(1.0, metrics.get("learning_packets", 0) / 6.0)
    peer_score = float(metrics.get("peer_ready_ratio") or 0.0)
    validation_score = float(metrics.get("validation_ready_ratio") or 0.0)
    outcome_base = min(1.0, metrics.get("outcomes_seen", 0) / 24.0)
    outcome_quality = 0.5 + float(metrics.get("outcome_pass_rate") or 0.0) * 0.5
    score = (
        edge_score * 0.22
        + relation_score * 0.12
        + packet_score * 0.16
        + peer_score * 0.22
        + validation_score * 0.12
        + outcome_base * outcome_quality * 0.16
    )
    if metrics.get("latest_age_hours", 999) > 24:
        score -= 0.12
    if metrics.get("council_age_hours", 999) > 18:
        score -= 0.06
    return round(max(0.0, min(1.0, score)), 3)


def collaboration_verdict(score: float, metrics: dict[str, Any]) -> str:
    if score >= 0.74 and metrics.get("peer_ready_ratio", 0) >= 0.65:
        return "collaboration_loop_active"
    if score >= 0.5:
        return "collaboration_scaffolding_improving"
    if metrics.get("learning_packets", 0):
        return "learning_packets_exist_but_files_not_yet_coworkers"
    return "no_live_file_collaboration_signal"


def operator_read(verdict: str, metrics: dict[str, Any]) -> str:
    if verdict == "collaboration_loop_active":
        return "Yes: the file sim is starting to behave like a collaboration loop, not just a selector."
    if verdict == "collaboration_scaffolding_improving":
        return "Yes, but with a caveat: files are coordinating through packets and edges; they are not yet negotiating through manifest state by default."
    if metrics.get("learning_packets", 0):
        return "Partly: files wake and learn, but the operator-readable collaboration layer is still missing teeth."
    return "No: there is not enough live sim state to claim collaboration yet."


def improvement_notes(metrics: dict[str, Any]) -> list[str]:
    notes = []
    if metrics.get("relationship_edges", 0):
        notes.append(f"relationship graph exists with {metrics.get('relationship_edges')} edge(s) across {metrics.get('relation_types')} relation type(s)")
    if metrics.get("learning_packets", 0):
        notes.append(f"{metrics.get('learning_packets')} learning packet(s) give files persistent responsibility, peers, and validation hints")
    if metrics.get("outcomes_seen", 0):
        notes.append(f"{metrics.get('outcomes_seen')} outcome record(s) can reward or punish future routing")
    if metrics.get("edge_trend") == "rising":
        notes.append("edge history is rising, so the sim is gaining relationship density")
    return notes or ["no clear improvement signal yet"]


def missing_loops(metrics: dict[str, Any]) -> list[str]:
    missing = []
    if metrics.get("peer_ready_ratio", 0) < 0.7:
        missing.append("make peer agreement a first-class manifest field, not an inferred side effect")
    if metrics.get("relation_types", 0) < 4:
        missing.append("add typed agreement/conflict/owner/blocker edges so files can derank bad peers")
    if metrics.get("validation_ready_ratio", 0) < 0.8:
        missing.append("require each file comment to name the test or compile gate it accepts")
    if metrics.get("outcomes_seen", 0) < 10:
        missing.append("feed more accepted/failed mutation outcomes back into file_profiles")
    if metrics.get("council_age_hours", 999) > 18:
        missing.append("refresh file council jobs per prompt so old councils stop cosplaying as current intelligence")
    return missing or ["no major collaboration loop gap detected"]


def recommended_next_moves(metrics: dict[str, Any]) -> list[str]:
    moves = [
        "load logs/file_manifest_collaboration_state.json before context selection in the next sim",
        "let each waking file write one manifest comment: learned, plan, blocker, agrees_with",
        "reward comments after validation so relationship weights change from actual outcomes",
    ]
    if metrics.get("overcap_split_jobs", 0):
        moves.append("turn over-cap split jobs into DeepSeek split-plan tasks, not source overwrites")
    return moves


def edge_trend(values: list[int]) -> str:
    if len(values) < 2:
        return "unknown"
    if values[-1] > values[0]:
        return "rising"
    if values[-1] < values[0]:
        return "falling"
    return "flat"


def age_hours(ts: Any) -> float:
    try:
        parsed = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return round((datetime.now(timezone.utc) - parsed).total_seconds() / 3600.0, 3)
    except Exception:
        return 999.0


def file_age_hours(path: Path, fallback_ts: Any = None) -> float:
    if path.exists():
        then = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        return round((datetime.now(timezone.utc) - then).total_seconds() / 3600.0, 3)
    return age_hours(fallback_ts)


def _ratio(top: int, bottom: int) -> float:
    return round(float(top) / max(1, int(bottom)), 3)
