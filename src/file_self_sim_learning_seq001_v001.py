"""Learning-mode file self-sim orchestration.

This is the training substrate before autonomous overwrites. It wakes files
from numeric intent/profile signals, chains peer context, emits DeepSeek-ready
learning packets, and records file-local memory for a later approval-gated
rewrite pass.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "file_self_sim_learning/v1"
PACKET_SCHEMA = "deepseek_file_learning_packet/v1"
OUTCOME_SCHEMA = "file_self_sim_learning_outcome/v1"

STOP = {
    "the", "and", "for", "with", "that", "this", "from", "into", "should",
    "would", "could", "have", "make", "work", "working", "actual", "using",
    "based", "time", "over", "all", "about", "then", "than", "their",
    "there", "what", "when", "where", "which", "want", "need", "needs",
    "themselves",
}

ALIASES = {
    "sims": "sim",
    "simulation": "sim",
    "simulations": "sim",
    "simulated": "sim",
    "simulating": "sim",
    "neumeric": "numeric",
    "neumaric": "numeric",
    "deepseekk": "deepseek",
    "knowlege": "knowledge",
    "manofest": "manifest",
}

DEFAULT_CONFIG = {
    "mode": "learning_only_no_overwrite",
    "max_packets": 8,
    "token_budget": 24000,
    "overwrite_allowed": False,
    "target_state": "interlinked_source_state",
    "deepseek_packet_policy": "draft_only_until_operator_approval",
    "update_file_profiles": True,
}


def simulate_file_self_learning(
    root: Path,
    intent: str = "",
    limit: int | None = None,
    write: bool = True,
    source_result: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the learning-only self-sim pass.

    No source file is overwritten here. The output is a set of durable learning
    packets and profile updates that a later approved rewrite pass can consume.
    """
    root = Path(root)
    settings = _merge_config(config)
    limit = int(limit or settings.get("max_packets") or 8)
    sources = _load_signal_sources(root, source_result)
    if intent and source_result is None:
        _drop_stale_runtime_sources(intent, sources)
    intent_model = _intent_model(root, intent, sources)
    candidates = _select_candidates(root, intent_model, sources, limit)
    wake_order = [
        _wake_node(root, row, index, intent_model, sources)
        for index, row in enumerate(candidates)
    ]
    diagnosis_flow = _diagnosis_flow(wake_order)
    packets = [
        _learning_packet(root, node, intent_model, sources, settings)
        for node in wake_order
    ]
    interlink_plan = _interlink_plan(root, wake_order, packets, intent_model, settings)
    result = {
        "schema": SCHEMA,
        "ts": _now(),
        "root": str(root),
        "mode": settings["mode"],
        "write_policy": "no_source_overwrite_learning_packets_only",
        "target_state": settings["target_state"],
        "intent": intent_model,
        "candidate_sources": sources["source_counts"],
        "wake_order": wake_order,
        "diagnosis_flow": diagnosis_flow,
        "learning_packets": packets,
        "interlink_plan": interlink_plan,
        "backward_learning_pass": _backward_learning_plan(packets),
        "paths": {
            "latest": "logs/file_self_sim_learning_latest.json",
            "history": "logs/file_self_sim_learning.jsonl",
            "markdown": "logs/file_self_sim_learning.md",
            "deepseek_learning_packets": "logs/deepseek_learning_packets.jsonl",
            "profiles": "file_profiles.json",
            "outcomes": "logs/file_self_sim_learning_outcomes.jsonl",
        },
    }
    if write:
        _write_learning_outputs(root, result, settings)
    return result


def simulate_file_learning_mode(*args: Any, **kwargs: Any) -> dict[str, Any]:
    """Compatibility alias for callers that use the earlier name."""
    return simulate_file_self_learning(*args, **kwargs)


def record_file_learning_outcome(
    root: Path,
    packet_id: str,
    outcome: str,
    reward: float = 0.0,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Record the backward-learning pass after grader/execution feedback."""
    root = Path(root)
    latest = _load_json(root / "logs" / "file_self_sim_learning_latest.json") or {}
    packet = next(
        (
            item for item in latest.get("learning_packets", [])
            if item.get("packet_id") == packet_id
        ),
        {},
    )
    record = {
        "schema": OUTCOME_SCHEMA,
        "ts": _now(),
        "packet_id": packet_id,
        "file": packet.get("file", ""),
        "intent_key": (latest.get("intent") or {}).get("intent_key", ""),
        "outcome": str(outcome or "unknown"),
        "reward": round(float(reward or 0.0), 4),
        "details": details or {},
        "backward_targets": packet.get("backward_learning_targets", []),
    }
    _append_jsonl(root / "logs" / "file_self_sim_learning_outcomes.jsonl", record)
    _apply_outcome_to_profiles(root, record)
    return record


def _merge_config(config: dict[str, Any] | None) -> dict[str, Any]:
    merged = json.loads(json.dumps(DEFAULT_CONFIG))
    for key, value in (config or {}).items():
        if key in merged:
            merged[key] = value
    merged["mode"] = "learning_only_no_overwrite"
    merged["overwrite_allowed"] = False
    return merged


def _load_signal_sources(root: Path, source_result: dict[str, Any] | None) -> dict[str, Any]:
    logs = root / "logs"
    latest = source_result or _load_json(logs / "batch_rewrite_sim_latest.json") or {}
    council = latest.get("file_job_council") or _load_json(logs / "file_job_council_latest.json") or {}
    memory_index = _load_json(logs / "file_memory_index.json") or {}
    file_profiles = _load_json(root / "file_profiles.json") or {}
    identity_growth = _load_jsonl(logs / "file_identity_growth.jsonl", 400)
    dead_pairs = _load_jsonl(logs / "dead_token_collective_pairs.jsonl", 400)
    intent_latest = _load_json(logs / "intent_key_latest.json") or {}
    numeric = _load_numeric_surface(root)
    return {
        "source_result_present": source_result is not None,
        "latest": latest,
        "council": council,
        "memory_index": memory_index,
        "file_profiles": file_profiles,
        "identity_growth": identity_growth,
        "dead_pairs": dead_pairs,
        "intent_latest": intent_latest,
        "numeric": numeric,
        "source_counts": {
            "proposals": len(latest.get("proposals") or []),
            "council_jobs": len(council.get("jobs") or []),
            "memory_files": len(memory_index.get("files") or []),
            "identity_growth": len(identity_growth),
            "history_pairs": len(dead_pairs),
            "numeric_files": len((numeric.get("matrix") or {})),
        },
    }


def _drop_stale_runtime_sources(intent: str, sources: dict[str, Any]) -> None:
    latest_intent = (sources.get("latest") or {}).get("intent") or {}
    latest_raw = str(latest_intent.get("raw") or (sources.get("intent_latest") or {}).get("prompt") or "")
    if not latest_raw:
        return
    current = set(_tokens(intent))
    previous = set(_tokens(latest_raw))
    if not current or not previous:
        return
    overlap = len(current & previous) / max(1, min(len(current), len(previous)))
    if overlap >= 0.35:
        return
    sources["latest"] = {"stale_runtime_source": latest_intent.get("intent_key", "")}
    sources["council"] = {}
    counts = sources.get("source_counts") or {}
    counts["proposals"] = 0
    counts["council_jobs"] = 0
    counts["stale_runtime_sources_dropped"] = 1
    sources["source_counts"] = counts


def _intent_model(root: Path, intent: str, sources: dict[str, Any]) -> dict[str, Any]:
    latest_intent = (sources.get("latest") or {}).get("intent") or {}
    intent_latest = sources.get("intent_latest") or {}
    raw = (
        intent
        or latest_intent.get("raw")
        or intent_latest.get("prompt")
        or intent_latest.get("raw")
        or ""
    ).strip()
    tokens = _tokens(raw)
    if intent and not sources.get("source_result_present"):
        intent_key = _fallback_intent_key(tokens)
    else:
        intent_key = (
            latest_intent.get("intent_key")
            or intent_latest.get("intent_key")
            or _fallback_intent_key(tokens)
        )
    explicit_intent = bool(intent and not sources.get("source_result_present"))
    unique_tokens = _dedupe(tokens)
    return {
        "raw": raw,
        "tokens": tokens[:80],
        "intent_key": intent_key,
        "scope": "root" if explicit_intent else latest_intent.get("scope") or intent_latest.get("scope") or "root",
        "target": "_".join(unique_tokens[:5]) if explicit_intent else latest_intent.get("target") or intent_latest.get("target") or "_".join(unique_tokens[:5]),
        "scale": ("major" if "rewrite" in tokens or "overwrite" in tokens else "patch") if explicit_intent else latest_intent.get("scale") or ("major" if "rewrite" in tokens else "patch"),
        "numeric_prompt_encoding": _prompt_numeric_encoding(root, raw, sources),
    }


def _select_candidates(
    root: Path,
    intent_model: dict[str, Any],
    sources: dict[str, Any],
    limit: int,
) -> list[dict[str, Any]]:
    bucket: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"score": 0.0, "reasons": [], "proposal": {}, "signals": Counter()}
    )
    _seed_from_proposals(bucket, sources)
    _seed_from_council(bucket, sources)
    _seed_from_memory(bucket, sources)
    _seed_from_identity_growth(bucket, sources, intent_model)
    _seed_from_dead_pairs(bucket, sources, intent_model)
    _seed_from_numeric_surface(root, bucket, sources, intent_model)
    _seed_from_path_tokens(root, bucket, intent_model)
    if not bucket:
        _seed_from_prompt_contract_fallback(root, bucket)
    rows = []
    for rel, data in bucket.items():
        rel = _clean_rel(rel)
        if not rel or not _candidate_allowed(root, rel):
            continue
        data["file"] = rel
        data["score"] = round(float(data["score"]), 4)
        data["signals"] = dict(data["signals"])
        data["reasons"] = _dedupe(data["reasons"])[:8]
        rows.append(data)
    rows.sort(
        key=lambda item: (
            item["score"] + _source_wake_bonus(item["file"]),
            item["score"],
            _exists_bonus(root, item["file"]),
        ),
        reverse=True,
    )
    return rows[: max(limit, 1)]


def _seed_from_prompt_contract_fallback(root: Path, bucket: dict[str, dict[str, Any]]) -> None:
    for rel in [
        "codex_compat.py",
        "src/batch_rewrite_sim_seq001_v001.py",
        "src/file_self_sim_learning_seq001_v001.py",
        "src/file_email_plugin_seq001_v001.py",
        "src/intent_loop_closer_seq001_v001.py",
    ]:
        if (root / rel).exists():
            _add(bucket, rel, 2.0, "prompt contract fallback woke core self-fix file", "prompt_contract")


def _seed_from_proposals(bucket: dict[str, dict[str, Any]], sources: dict[str, Any]) -> None:
    for index, proposal in enumerate((sources.get("latest") or {}).get("proposals") or []):
        rel = _clean_rel(proposal.get("path"))
        if not rel:
            continue
        points = 9.0 - index * 0.35
        points += float(proposal.get("confidence") or 0) * 2.0
        points += float(proposal.get("interlink_score") or 0) * 2.0
        _add(bucket, rel, points, "batch proposal survived intent/history ranking", "proposal")
        bucket[rel]["proposal"] = proposal


def _seed_from_council(bucket: dict[str, dict[str, Any]], sources: dict[str, Any]) -> None:
    council = sources.get("council") or {}
    for job in council.get("jobs") or []:
        captain = _clean_rel(job.get("captain"))
        if captain:
            _add(bucket, captain, 3.5, "job captain should wake first", "council")
        for rel in (job.get("files") or [])[:12]:
            _add(bucket, rel, 2.4, "job member in same work cell", "council")
        for rel in (job.get("context_files") or [])[:12]:
            _add(bucket, rel, 1.1, "context vein from job council", "council")
    for pack in council.get("context_packs") or []:
        for rel in (pack.get("files") or [])[:16]:
            _add(bucket, rel, 0.9, f"context pack {pack.get('pack_id', 'unknown')}", "context_pack")


def _seed_from_memory(bucket: dict[str, dict[str, Any]], sources: dict[str, Any]) -> None:
    for item in (sources.get("memory_index") or {}).get("files") or []:
        rel = _clean_rel(item.get("file"))
        if rel:
            _add(bucket, rel, 2.0, "file has durable mail/thread memory", "memory")


def _seed_from_identity_growth(
    bucket: dict[str, dict[str, Any]],
    sources: dict[str, Any],
    intent_model: dict[str, Any],
) -> None:
    prompt_tokens = set(intent_model.get("tokens") or [])
    best_by_file: dict[str, float] = {}
    for row in (sources.get("identity_growth") or [])[-120:]:
        rel = _clean_rel(row.get("file"))
        if not rel:
            continue
        growth_tags = set(str(tag) for tag in row.get("growth_tags") or [])
        overlap = len(prompt_tokens & growth_tags)
        path_overlap = len(prompt_tokens & set(_tokens(rel)))
        points = 0.8 + overlap * 0.18 + float(row.get("interlink_score") or 0) * 1.3
        if path_overlap:
            points += path_overlap * 0.6
        else:
            points *= 0.35
        best_by_file[rel] = max(best_by_file.get(rel, 0.0), points)
    for rel, points in best_by_file.items():
        _add(bucket, rel, points, "identity growth remembers similar intent tags", "identity_growth")


def _seed_from_dead_pairs(
    bucket: dict[str, dict[str, Any]],
    sources: dict[str, Any],
    intent_model: dict[str, Any],
) -> None:
    prompt_tokens = set(intent_model.get("tokens") or [])
    for row in (sources.get("dead_pairs") or [])[-160:]:
        rel = _clean_rel(row.get("new_path") or row.get("old_path"))
        if not rel:
            continue
        text = " ".join(str(row.get(key) or "") for key in ("subject", "prompt", "intent_key"))
        overlap = len(prompt_tokens & set(_tokens(text)))
        if overlap or rel in bucket:
            _add(bucket, rel, 0.5 + overlap * 0.25, "rename/change history predicts this file", "history")


def _seed_from_numeric_surface(
    root: Path,
    bucket: dict[str, dict[str, Any]],
    sources: dict[str, Any],
    intent_model: dict[str, Any],
) -> None:
    for item in _numeric_predictions(root, intent_model, sources)[:16]:
        rel = _clean_rel(item.get("file"))
        if rel:
            _add(bucket, rel, 1.5 + float(item.get("score") or 0) * 4.0, "numeric prompt encoding selected file", "numeric")


def _seed_from_path_tokens(root: Path, bucket: dict[str, dict[str, Any]], intent_model: dict[str, Any]) -> None:
    prompt_tokens = set(intent_model.get("tokens") or [])
    if not prompt_tokens:
        return
    for rel in _scan_repo_files(root):
        overlap = prompt_tokens & set(_tokens(rel))
        if len(overlap) >= 2:
            points = 2.0 + len(overlap) * 1.1
            if len(overlap) >= 3:
                points += 4.0
            _add(bucket, rel, points, "path tokens match current intent", "path")


def _wake_node(
    root: Path,
    row: dict[str, Any],
    index: int,
    intent_model: dict[str, Any],
    sources: dict[str, Any],
) -> dict[str, Any]:
    rel = row["file"]
    proposal = row.get("proposal") or {}
    memory = _memory_for_file(root, rel, sources)
    profile = _profile_for_file(rel, sources)
    growth = _growth_for_file(rel, sources)
    neighbors = _neighbors_for_file(rel, proposal, sources)
    tests = _tests_for_file(root, rel, proposal)
    learned = _learned_enough(memory, profile, growth, proposal, tests)
    role = _wake_role(index, rel, proposal, neighbors, tests)
    basis = json.dumps({
        "intent": intent_model.get("intent_key"),
        "file": rel,
        "memory": memory.get("summary", ""),
        "neighbors": neighbors[:8],
        "tests": tests[:5],
    }, sort_keys=True)
    return {
        "sequence": index + 1,
        "file": rel,
        "role": role,
        "wake_score": row["score"],
        "wake_reason": "; ".join(row.get("reasons") or [])[:240],
        "signals": row.get("signals", {}),
        "numeric_encoding": _hash_encoding(basis),
        "responsibility_profile": _responsibility_profile(root, rel, memory, profile, growth),
        "known_neighbors": neighbors[:12],
        "context_veins": _context_veins(rel, neighbors, sources),
        "manifest": _nearest_manifest(root, rel),
        "tests": tests[:8],
        "estimated_tokens": _estimate_tokens(root, rel),
        "learned_enough": learned,
        "next_question": _next_question(role, learned, neighbors, tests),
    }


def _learning_packet(
    root: Path,
    node: dict[str, Any],
    intent_model: dict[str, Any],
    sources: dict[str, Any],
    settings: dict[str, Any],
) -> dict[str, Any]:
    rel = node["file"]
    proposal = ((sources.get("latest") or {}).get("proposals_by_file") or {}).get(rel) or {}
    if not proposal:
        proposal = _proposal_for_file(rel, sources)
    packet_seed = json.dumps({
        "intent": intent_model.get("intent_key"),
        "file": rel,
        "encoding": node.get("numeric_encoding", {}).get("signature"),
    }, sort_keys=True)
    packet_id = "dslp-" + hashlib.sha256(packet_seed.encode("utf-8")).hexdigest()[:16]
    validation = proposal.get("cross_file_validation") or {}
    validation_plan = proposal.get("validation_plan") or _default_validation(root, rel, node.get("tests") or [])
    readiness = _overwrite_readiness(node, proposal, settings)
    return {
        "schema": PACKET_SCHEMA,
        "packet_id": packet_id,
        "file": rel,
        "intent_key": intent_model.get("intent_key", ""),
        "mode": settings["mode"],
        "target_state": settings["target_state"],
        "wake_role": node.get("role"),
        "numeric_encoding": node.get("numeric_encoding"),
        "responsibility_profile": node.get("responsibility_profile"),
        "intent_profile": {
            "tokens": intent_model.get("tokens", [])[:32],
            "selected_by": node.get("signals", {}),
            "wake_score": node.get("wake_score", 0),
            "current_question": node.get("next_question"),
        },
        "accumulated_knowledge": _accumulated_knowledge(rel, sources),
        "context_veins": node.get("context_veins", []),
        "verification_packet": {
            "validation_plan": validation_plan,
            "tests": node.get("tests", []),
            "imports_seen": validation.get("imports", []),
            "referenced_by": validation.get("referenced_by", []),
            "dirty": validation.get("dirty", False),
        },
        "overwrite_readiness": readiness,
        "deepseek_instruction": _deepseek_learning_instruction(rel, intent_model, node, validation_plan, readiness),
        "backward_learning_targets": _backward_targets(rel, node),
    }


def _diagnosis_flow(wake_order: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not wake_order:
        return []
    top = wake_order[0]["file"]
    return [
        {
            "stage": "wake",
            "owner": top,
            "action": "select top file by numeric intent, history, memory, and profile signals",
        },
        {
            "stage": "load_identity",
            "owner": top,
            "action": "load file profile, mail memory, prior sim outcomes, manifest, and tests",
        },
        {
            "stage": "sequence_peers",
            "owner": "orchestrator",
            "action": "order peer files by context veins before rewrite planning",
            "files": [item["file"] for item in wake_order],
        },
        {
            "stage": "diagnose",
            "owner": "file_council",
            "action": "each file states responsibility, missing context, and validation gate",
        },
        {
            "stage": "emit_packets",
            "owner": "deepseek_learning_queue",
            "action": "write draft-only learning packets for deep rewrite reasoning",
        },
        {
            "stage": "approval_gate",
            "owner": "operator",
            "action": "no source overwrite until approval plus compile/test gate exists",
        },
        {
            "stage": "backward_learning",
            "owner": "file_profiles",
            "action": "record reward, failure reason, and sibling effects after execution",
        },
    ]


def _interlink_plan(
    root: Path,
    wake_order: list[dict[str, Any]],
    packets: list[dict[str, Any]],
    intent_model: dict[str, Any],
    settings: dict[str, Any],
) -> dict[str, Any]:
    manifests: dict[str, list[str]] = defaultdict(list)
    for node in wake_order:
        manifest = node.get("manifest") or "root"
        manifests[manifest].append(node["file"])
    missing_tests = [
        node["file"] for node in wake_order
        if node["file"].endswith(".py") and not node.get("tests")
    ]
    return {
        "goal": settings["target_state"],
        "intent_key": intent_model.get("intent_key", ""),
        "manifest_chains": [
            {"manifest": manifest, "files": files[:12], "action": "keep responsibilities explicit before rewrite"}
            for manifest, files in sorted(manifests.items())
        ],
        "near_term_jobs": [
            {
                "job": "build_learning_profiles",
                "files": [packet["file"] for packet in packets[:6]],
                "action": "accumulate enough profile, memory, and test evidence before self-overwrite",
            },
            {
                "job": "close_validation_gaps",
                "files": missing_tests[:8],
                "action": "add or map compile/test gates before autonomous patch eligibility",
            },
            {
                "job": "prepare_deepseek_context_pack",
                "files": _context_pack_files(root, wake_order),
                "action": "load top waker, manifest, tests, and highest-friction peers",
            },
        ],
        "overwrite_gate": {
            "allowed_now": False,
            "future_requirements": [
                "operator approval",
                "DeepSeek packet generated",
                "context veins fulfilled",
                "10Q/validation packet passed",
                "compile/test result recorded through backward learning",
            ],
        },
    }


def _backward_learning_plan(packets: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "status": "armed_waiting_for_outcome",
        "record_function": "record_file_learning_outcome(root, packet_id, outcome, reward, details)",
        "on_success": [
            "increase selected file intent/profile affinity",
            "strengthen context vein edges that were loaded",
            "mark validation packet as trusted for similar future intent",
        ],
        "on_failure": [
            "lower selected file affinity for this intent cluster",
            "record missing context or incompatible peer",
            "wake validator earlier in the next sequence",
        ],
        "packet_ids": [packet.get("packet_id") for packet in packets],
    }


def _write_learning_outputs(root: Path, result: dict[str, Any], settings: dict[str, Any]) -> None:
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    _write_json(logs / "file_self_sim_learning_latest.json", result)
    _append_jsonl(logs / "file_self_sim_learning.jsonl", result)
    (logs / "file_self_sim_learning.md").write_text(_render_learning_markdown(result), encoding="utf-8")
    for packet in result.get("learning_packets") or []:
        _append_jsonl(logs / "deepseek_learning_packets.jsonl", packet)
    if settings.get("update_file_profiles", True):
        _update_file_profiles(root, result)
    try:
        from src.file_email_plugin_seq001_v001 import emit_learning_digest_email
        result["learning_digest_email"] = emit_learning_digest_email(root, result)
        _write_json(logs / "file_self_sim_learning_latest.json", result)
    except Exception as exc:
        result["learning_digest_email_error"] = str(exc)
        _write_json(logs / "file_self_sim_learning_latest.json", result)


def _update_file_profiles(root: Path, result: dict[str, Any]) -> None:
    profiles = _load_json(root / "file_profiles.json") or {}
    ts = result.get("ts") or _now()
    intent_key = (result.get("intent") or {}).get("intent_key", "")
    for packet in result.get("learning_packets") or []:
        rel = packet.get("file", "")
        key = _stem_key(rel)
        profile = profiles.setdefault(key, {})
        history = profile.setdefault("learning_history", [])
        history.append({
            "ts": ts,
            "packet_id": packet.get("packet_id"),
            "file": rel,
            "intent_key": intent_key,
            "mode": result.get("mode"),
            "wake_role": packet.get("wake_role"),
            "wake_score": (packet.get("intent_profile") or {}).get("wake_score", 0),
            "overwrite_readiness": packet.get("overwrite_readiness", {}),
        })
        profile["learning_history"] = history[-30:]
        profile["self_sim_profile"] = {
            "file": rel,
            "responsibility_profile": packet.get("responsibility_profile", {}),
            "context_veins": packet.get("context_veins", []),
            "verification_packet": packet.get("verification_packet", {}),
            "last_packet_id": packet.get("packet_id"),
            "target_state": result.get("target_state"),
        }
        profile["self_repair_hint"] = _profile_hint(packet)
        profile["overwrite_readiness"] = packet.get("overwrite_readiness", {})
        watch = profile.setdefault("backwards_pass_watch", [])
        for target in packet.get("backward_learning_targets") or []:
            file_name = target.get("file") if isinstance(target, dict) else str(target)
            if file_name and file_name not in watch:
                watch.insert(0, file_name)
        profile["backwards_pass_watch"] = watch[:12]
        profiles[key] = profile
    _write_json(root / "file_profiles.json", profiles)


def _apply_outcome_to_profiles(root: Path, record: dict[str, Any]) -> None:
    profiles = _load_json(root / "file_profiles.json") or {}
    touched = [record.get("file"), *[
        item.get("file") for item in record.get("backward_targets", [])
        if isinstance(item, dict)
    ]]
    for rel in _dedupe(touched):
        if not rel:
            continue
        key = _stem_key(rel)
        profile = profiles.setdefault(key, {})
        outcomes = profile.setdefault("learning_outcomes", [])
        outcomes.append({
            "ts": record.get("ts"),
            "packet_id": record.get("packet_id"),
            "outcome": record.get("outcome"),
            "reward": record.get("reward"),
            "intent_key": record.get("intent_key"),
        })
        profile["learning_outcomes"] = outcomes[-30:]
    _write_json(root / "file_profiles.json", profiles)


def _render_learning_markdown(result: dict[str, Any]) -> str:
    intent = result.get("intent") or {}
    lines = [
        "# File Self-Sim Learning Mode",
        "",
        "This is not a notification lane. It is the learning-only substrate for approval-gated self-overwrite.",
        "",
        "```text",
        f"intent_key: {intent.get('intent_key', '')}",
        f"mode: {result.get('mode')}",
        f"target_state: {result.get('target_state')}",
        "source_overwrite: blocked until approval and validation",
        "```",
        "",
        "## Wake Order",
        "",
    ]
    for node in result.get("wake_order", [])[:12]:
        lines.append(
            f"{node.get('sequence')}. `{node.get('file')}` - {node.get('role')} "
            f"(score {node.get('wake_score')})"
        )
        lines.append(f"   - why: {node.get('wake_reason') or 'selected by profile signals'}")
        lines.append(f"   - next: {node.get('next_question')}")
    lines.extend(["", "## Diagnosis Flow", ""])
    for step in result.get("diagnosis_flow", []):
        lines.append(f"- `{step.get('stage')}` by `{step.get('owner')}`: {step.get('action')}")
    lines.extend(["", "## Learning Packets", ""])
    for packet in result.get("learning_packets", [])[:10]:
        readiness = packet.get("overwrite_readiness") or {}
        lines.append(f"### {packet.get('file')}")
        lines.append(f"- packet: `{packet.get('packet_id')}`")
        lines.append(f"- readiness: `{readiness.get('state')}` - {readiness.get('reason')}")
        lines.append(
            "- context veins: "
            + (", ".join(f"`{item.get('file')}`" for item in packet.get("context_veins", [])[:6]) or "none")
        )
        lines.append(
            "- validation: "
            + (", ".join(f"`{item}`" for item in (packet.get("verification_packet") or {}).get("validation_plan", [])[:4]) or "none")
        )
        lines.append("")
    plan = result.get("interlink_plan") or {}
    lines.extend(["## Interlink Plan", ""])
    for job in plan.get("near_term_jobs", []):
        lines.append(f"- `{job.get('job')}`: {job.get('action')} ({len(job.get('files') or [])} file(s))")
    lines.extend(["", "## Backward Learning Pass", ""])
    back = result.get("backward_learning_pass") or {}
    lines.append(f"- status: `{back.get('status')}`")
    lines.append(f"- record: `{back.get('record_function')}`")
    return "\n".join(lines) + "\n"


def _responsibility_profile(
    root: Path,
    rel: str,
    memory: dict[str, Any],
    profile: dict[str, Any],
    growth: list[dict[str, Any]],
) -> dict[str, Any]:
    path_tokens = [token for token in _tokens(rel) if token not in {"src", "test", "seq", "v001"}]
    return {
        "file": rel,
        "stem": _stem_key(rel),
        "declared_role": _role_from_path(path_tokens),
        "path_terms": path_tokens[:12],
        "line_count": _line_count(root, rel),
        "memory_summary": memory.get("summary", "no durable memory yet"),
        "profile_hint": profile.get("self_repair_hint", ""),
        "growth_tags": _top_growth_tags(growth),
    }


def _accumulated_knowledge(rel: str, sources: dict[str, Any]) -> dict[str, Any]:
    memory = _memory_for_file(Path("."), rel, sources, allow_read=False)
    profile = _profile_for_file(rel, sources)
    growth = _growth_for_file(rel, sources)
    return {
        "mail_memory": memory,
        "profile_keys": sorted(profile.keys())[:12],
        "recent_identity_growth": growth[-5:],
        "history_events": _history_count_for_file(rel, sources),
    }


def _context_veins(rel: str, neighbors: list[str], sources: dict[str, Any]) -> list[dict[str, str]]:
    veins = []
    for neighbor in neighbors:
        if neighbor == rel:
            continue
        relation = _relationship_type(rel, neighbor, sources)
        veins.append({"file": neighbor, "relation": relation, "reason": _vein_reason(relation)})
    return veins[:10]


def _backward_targets(rel: str, node: dict[str, Any]) -> list[dict[str, str]]:
    targets = [{"file": rel, "learn": "record direct reward and rewrite outcome"}]
    for neighbor in (node.get("known_neighbors") or [])[:6]:
        targets.append({"file": neighbor, "learn": "record sibling compatibility effect"})
    for test in (node.get("tests") or [])[:4]:
        targets.append({"file": test, "learn": "record validation effect"})
    return targets


def _deepseek_learning_instruction(
    rel: str,
    intent_model: dict[str, Any],
    node: dict[str, Any],
    validation_plan: list[str],
    readiness: dict[str, Any],
) -> str:
    context_files = [item.get("file") for item in node.get("context_veins", []) if item.get("file")]
    return "\n".join([
        "You are the deep rewrite planner for one source file.",
        "Do not overwrite source. Produce a plan or patch candidate only.",
        f"INTENT_KEY: {intent_model.get('intent_key', '')}",
        f"FILE: {rel}",
        f"WAKE_ROLE: {node.get('role')}",
        f"READINESS: {readiness.get('state')} - {readiness.get('reason')}",
        "LOAD_CONTEXT:",
        *[f"- {item}" for item in context_files[:10]],
        "VALIDATION:",
        *[f"- {item}" for item in validation_plan[:8]],
        "OUTPUT: responsibility diagnosis, minimal rewrite hypothesis, risks, validation command, backward-learning note.",
    ])


def _overwrite_readiness(node: dict[str, Any], proposal: dict[str, Any], settings: dict[str, Any]) -> dict[str, Any]:
    learned = node.get("learned_enough") or {}
    if not settings.get("overwrite_allowed", False):
        return {
            "state": "learning_only",
            "allowed": False,
            "reason": "overwrite is disabled until operator approval and validation outcome exist",
        }
    if not learned.get("enough_for_self_rewrite"):
        return {"state": "needs_more_memory", "allowed": False, "reason": learned.get("reason", "")}
    if proposal.get("approval_gate") != "operator_required":
        return {"state": "missing_operator_gate", "allowed": False, "reason": "approval gate not explicit"}
    return {"state": "ready_after_approval", "allowed": False, "reason": "approval still required"}


def _learned_enough(
    memory: dict[str, Any],
    profile: dict[str, Any],
    growth: list[dict[str, Any]],
    proposal: dict[str, Any],
    tests: list[str],
) -> dict[str, Any]:
    score = 0
    score += 1 if memory.get("messages", 0) else 0
    score += 1 if profile.get("learning_history") else 0
    score += 1 if growth else 0
    score += 1 if proposal else 0
    score += 1 if tests else 0
    enough = score >= 4 and bool(tests)
    return {
        "score": score,
        "enough_for_self_rewrite": enough,
        "reason": "has memory/history/profile/test evidence" if enough else "learning mode needs more memory or validation",
    }


def _memory_for_file(root: Path, rel: str, sources: dict[str, Any], allow_read: bool = True) -> dict[str, Any]:
    for item in (sources.get("memory_index") or {}).get("files") or []:
        if _clean_rel(item.get("file")) != rel:
            continue
        notes = []
        commands: dict[str, list[str]] = defaultdict(list)
        if allow_read:
            path = Path(item.get("path") or "")
            if not path.is_absolute():
                path = root / path
            data = _load_json(path) or {}
            for message in data.get("messages", [])[-12:]:
                for key, values in (message.get("commands") or {}).items():
                    for value in values or []:
                        commands[key].append(str(value))
                preview = str(message.get("body_preview") or "").strip()
                if preview and len(notes) < 4:
                    notes.append(preview[:180])
        command_summary = {
            key: _dedupe(values)[-5:]
            for key, values in commands.items()
        }
        summary_bits = []
        for key in ("remember", "use", "avoid", "style"):
            if command_summary.get(key):
                summary_bits.append(f"{key}: {command_summary[key][-1]}")
        return {
            "messages": int(item.get("messages") or 0),
            "thread": item.get("markdown") or item.get("path") or "",
            "commands": command_summary,
            "notes": notes,
            "summary": "; ".join(summary_bits) or f"{item.get('messages', 0)} stored message(s)",
        }
    return {"messages": 0, "thread": "", "commands": {}, "notes": [], "summary": "no durable memory yet"}


def _profile_for_file(rel: str, sources: dict[str, Any]) -> dict[str, Any]:
    profiles = sources.get("file_profiles") or {}
    return profiles.get(_stem_key(rel), {})


def _growth_for_file(rel: str, sources: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        row for row in (sources.get("identity_growth") or [])
        if _clean_rel(row.get("file")) == rel
    ][-12:]


def _history_count_for_file(rel: str, sources: dict[str, Any]) -> int:
    return sum(
        1 for row in (sources.get("dead_pairs") or [])
        if _clean_rel(row.get("new_path") or row.get("old_path")) == rel
    )


def _neighbors_for_file(rel: str, proposal: dict[str, Any], sources: dict[str, Any]) -> list[str]:
    neighbors: list[str] = []
    neighbors.extend(_clean_rel(item) for item in proposal.get("context_injection") or [])
    validation = proposal.get("cross_file_validation") or {}
    neighbors.extend(_clean_rel(item) for item in validation.get("referenced_by") or [])
    for edge in (sources.get("council") or {}).get("relationships") or []:
        left = _clean_rel(edge.get("from"))
        right = _clean_rel(edge.get("to"))
        if left == rel:
            neighbors.append(right)
        elif right == rel:
            neighbors.append(left)
    for pack in (sources.get("council") or {}).get("context_packs") or []:
        files = [_clean_rel(item) for item in pack.get("files") or []]
        if rel in files:
            neighbors.extend(files)
    return [item for item in _dedupe(neighbors) if item and item != rel][:16]


def _proposal_for_file(rel: str, sources: dict[str, Any]) -> dict[str, Any]:
    for proposal in (sources.get("latest") or {}).get("proposals") or []:
        if _clean_rel(proposal.get("path")) == rel:
            return proposal
    return {}


def _wake_role(index: int, rel: str, proposal: dict[str, Any], neighbors: list[str], tests: list[str]) -> str:
    if index == 0:
        return "top_waker"
    if rel.lower().endswith("manifest.md"):
        return "manifest_anchor"
    if Path(rel).name.startswith("test_") or "/test" in rel:
        return "validator"
    ten_q = proposal.get("ten_q") or {}
    if ten_q and not ten_q.get("passed", True):
        return "blocker"
    if tests:
        return "diagnoser"
    if neighbors:
        return "peer_context"
    return "learner"


def _next_question(role: str, learned: dict[str, Any], neighbors: list[str], tests: list[str]) -> str:
    if role == "top_waker":
        return "Which peer must wake next before I draft a rewrite?"
    if not tests:
        return "Which validation gate proves my rewrite survived?"
    if not learned.get("enough_for_self_rewrite"):
        return "What memory or history do I need before self-overwrite eligibility?"
    if neighbors:
        return f"Does {Path(neighbors[0]).name} conflict with my planned change?"
    return "Can I emit a bounded DeepSeek rewrite packet after approval?"


def _default_validation(root: Path, rel: str, tests: list[str]) -> list[str]:
    path = root / rel
    plan = []
    if path.suffix == ".py":
        plan.append(f"py -m py_compile {rel}")
    plan.extend(f"py -m pytest {test} -q" for test in tests[:3])
    if not plan:
        plan.append("git diff --check")
    return plan


def _tests_for_file(root: Path, rel: str, proposal: dict[str, Any]) -> list[str]:
    tests = []
    for step in proposal.get("validation_plan") or []:
        for match in re.findall(r"((?:tests?/)?test[a-zA-Z0-9_./\\-]+\.py)", str(step)):
            tests.append(_clean_rel(match))
    stem = _stem_key(rel)
    candidates = [
        root / f"test_{stem}.py",
        root / "tests" / f"test_{stem}.py",
    ]
    for path in candidates:
        if path.exists():
            tests.append(path.relative_to(root).as_posix())
    return _dedupe(tests)


def _nearest_manifest(root: Path, rel: str) -> str:
    current = (root / rel).parent
    while current != root and root in current.parents:
        manifest = current / "MANIFEST.md"
        if manifest.exists():
            return manifest.relative_to(root).as_posix()
        current = current.parent
    manifest = root / "src" / "MANIFEST.md"
    if manifest.exists():
        return manifest.relative_to(root).as_posix()
    return ""


def _context_pack_files(root: Path, wake_order: list[dict[str, Any]]) -> list[str]:
    files = []
    for node in wake_order[:4]:
        files.append(node["file"])
        if node.get("manifest"):
            files.append(node["manifest"])
        files.extend(node.get("tests") or [])
        files.extend(node.get("known_neighbors") or [])
    budget = 24000
    total = 0
    packed = []
    for rel in _dedupe(files):
        tokens = _estimate_tokens(root, rel)
        if total + tokens > budget and packed:
            continue
        packed.append(rel)
        total += tokens
    return packed[:16]


def _numeric_predictions(root: Path, intent_model: dict[str, Any], sources: dict[str, Any]) -> list[dict[str, Any]]:
    numeric = sources.get("numeric") or {}
    vocab = numeric.get("vocab") or {}
    matrix = numeric.get("matrix") or {}
    ids = [str(vocab.get(token)) for token in intent_model.get("tokens", []) if vocab.get(token)]
    if not ids:
        return []
    predictions = []
    resolver = _file_key_resolver(root)
    for file_key, weights in matrix.items():
        score = 0.0
        for wid in ids:
            score += float(weights.get(wid) or 0)
        if score <= 0:
            continue
        rel = resolver.get(file_key) or _resolve_file_key(root, file_key)
        if rel:
            predictions.append({"file_key": file_key, "file": rel, "score": round(score, 5)})
    predictions.sort(key=lambda item: item["score"], reverse=True)
    return predictions


def _prompt_numeric_encoding(root: Path, raw: str, sources: dict[str, Any]) -> dict[str, Any]:
    numeric = sources.get("numeric") or {}
    vocab = numeric.get("vocab") or {}
    words = _tokens(raw)
    ids = [int(vocab[word]) for word in words if word in vocab]
    return {
        "method": "intent_vocab_ids_plus_sha256_signature",
        "known_token_ids": ids[:40],
        "unknown_tokens": [word for word in words if word not in vocab][:20],
        "signature": hashlib.sha256("|".join(words).encode("utf-8")).hexdigest()[:16],
    }


def _load_numeric_surface(root: Path) -> dict[str, Any]:
    vocab_data = _load_json(root / "logs" / "intent_vocab.json") or {}
    matrix_data = _load_json(root / "logs" / "intent_matrix.json") or {}
    return {
        "vocab": vocab_data.get("word_to_id") or {},
        "matrix": matrix_data.get("matrix") or {},
    }


def _file_key_resolver(root: Path) -> dict[str, str]:
    resolver = {}
    for rel in _scan_repo_files(root):
        stem = _stem_key(rel)
        resolver[stem] = rel
        resolver[Path(rel).stem] = rel
    return resolver


def _resolve_file_key(root: Path, file_key: str) -> str:
    target = _stem_key(file_key)
    for rel in _scan_repo_files(root):
        stem = _stem_key(rel)
        if stem == target or Path(rel).stem.startswith(file_key):
            return rel
    return ""


def _scan_repo_files(root: Path) -> list[str]:
    patterns = [
        "src/**/*.py",
        "client/**/*.py",
        "test*.py",
        "tests/**/*.py",
        "src/**/MANIFEST.md",
        ".github/copilot-instructions.md",
    ]
    files = []
    for pattern in patterns:
        for path in root.glob(pattern):
            rel = path.relative_to(root).as_posix()
            if "/__pycache__/" in rel or rel.startswith("logs/"):
                continue
            files.append(rel)
    return _dedupe(files)


def _candidate_allowed(root: Path, rel: str) -> bool:
    suffix = Path(rel).suffix.lower()
    if suffix not in {".py", ".md"}:
        return False
    if rel.startswith("logs/") or "/__pycache__/" in rel:
        return False
    return (root / rel).exists()


def _role_from_path(tokens: list[str]) -> str:
    if "test" in tokens or "validation" in tokens:
        return "validation and survival gate"
    if "intent" in tokens:
        return "intent compilation and routing"
    if "sim" in tokens or "simulation" in tokens:
        return "file simulation and grading"
    if "email" in tokens or "memory" in tokens:
        return "file memory and durable conversation"
    if "deepseek" in tokens:
        return "deep rewrite model queue"
    if "manifest" in tokens:
        return "scope constitution and file ownership"
    return "source responsibility inferred from path and history"


def _relationship_type(rel: str, neighbor: str, sources: dict[str, Any]) -> str:
    for edge in (sources.get("council") or {}).get("relationships") or []:
        left = _clean_rel(edge.get("from"))
        right = _clean_rel(edge.get("to"))
        if {left, right} == {rel, neighbor}:
            return str(edge.get("type") or "peer")
    if Path(neighbor).name.startswith("test_"):
        return "validator"
    if neighbor.lower().endswith("manifest.md"):
        return "manifest"
    return "peer_context"


def _vein_reason(relation: str) -> str:
    return {
        "friendship": "load together; prior council says they cooperate",
        "beef": "load together; rewrite order or layout may conflict",
        "validator": "test gate should judge the rewrite",
        "manifest": "scope responsibility must stay explicit",
    }.get(relation, "peer context affects diagnosis")


def _top_growth_tags(growth: list[dict[str, Any]]) -> list[str]:
    counts: Counter[str] = Counter()
    for row in growth:
        counts.update(str(tag) for tag in row.get("growth_tags") or [])
    return [tag for tag, _count in counts.most_common(12)]


def _hash_encoding(text: str) -> dict[str, Any]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    vector = [int.from_bytes(digest[i:i + 2], "big") for i in range(0, 16, 2)]
    return {
        "method": "sha256_u16_file_intent_profile",
        "signature": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16],
        "vector_u16": vector,
    }


def _profile_hint(packet: dict[str, Any]) -> str:
    veins = [item.get("file") for item in packet.get("context_veins", [])[:3]]
    validation = (packet.get("verification_packet") or {}).get("validation_plan", [])
    return " ".join([
        f"For {packet.get('intent_key', '')}, load {', '.join(veins) or 'manifest/test context'} first.",
        f"Validate with {validation[0] if validation else 'git diff --check'}.",
        "Do not self-overwrite until approval and outcome reward are recorded.",
    ])[:360]


def _clean_rel(value: Any) -> str:
    text = str(value or "").strip().strip("'\"").replace("\\", "/")
    if not text or text.startswith("/") or (len(text) > 1 and text[1] == ":"):
        return ""
    if ".." in Path(text).parts:
        return ""
    return text


def _tokens(text: str) -> list[str]:
    out = []
    for raw in re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", str(text).lower()):
        expanded = [raw]
        if "_" in raw:
            expanded.extend(part for part in raw.split("_") if part)
        for token in expanded:
            token = token.strip("_")
            if len(token) >= 3 and token not in STOP:
                normalized = ALIASES.get(token, token)
                out.append(normalized)
                if normalized.endswith("s") and len(normalized) > 4:
                    out.append(normalized[:-1])
    return out


def _stem_key(rel: str) -> str:
    stem = Path(str(rel)).stem.lower()
    stem = re.sub(r"_seq\d+(?=_|$)", "", stem)
    stem = re.sub(r"_s\d{3}(?=_|$)", "", stem)
    stem = re.sub(r"_v\d+(?=_|$)", "", stem)
    stem = re.sub(r"_d\d{4}(?=_|$)", "", stem)
    stem = stem.split("__", 1)[0]
    stem = re.sub(r"[^a-z0-9_]+", "_", stem)
    return re.sub(r"_+", "_", stem).strip("_") or Path(str(rel)).stem.lower()


def _fallback_intent_key(tokens: list[str]) -> str:
    unique_tokens = _dedupe(tokens)
    unique_set = set(unique_tokens)
    target_tokens = [
        token for token in unique_tokens
        if not (token.endswith("s") and len(token) > 4 and token[:-1] in unique_set)
    ]
    verb = "build"
    if {"test", "validate", "verify"} & set(unique_tokens):
        verb = "validate"
    if {"rewrite", "overwrite", "patch", "fix"} & set(unique_tokens):
        verb = "patch"
    target = "_".join(target_tokens[:5])[:64] or "work"
    scale = "major" if {"rewrite", "overwrite", "batch"} & set(unique_tokens) else "patch"
    return f"root:{verb}:{target}:{scale}"


def _line_count(root: Path, rel: str) -> int:
    try:
        return len((root / rel).read_text(encoding="utf-8", errors="ignore").splitlines())
    except Exception:
        return 0


def _estimate_tokens(root: Path, rel: str) -> int:
    try:
        text = (root / rel).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return 0
    return max(1, len(text) // 4)


def _exists_bonus(root: Path, rel: str) -> int:
    return 1 if (root / rel).exists() else 0


def _source_wake_bonus(rel: str) -> float:
    path = str(rel).replace("\\", "/")
    name = Path(path).name
    if name.startswith("test_") or "/test" in path:
        return -1.5
    if path.startswith("src/"):
        return 3.0
    if path.startswith("client/"):
        return 2.0
    return 0.0


def _add(
    bucket: dict[str, dict[str, Any]],
    rel: Any,
    points: float,
    reason: str,
    signal: str,
) -> None:
    clean = _clean_rel(rel)
    if not clean:
        return
    bucket[clean]["score"] += float(points)
    bucket[clean]["reasons"].append(reason)
    bucket[clean]["signals"][signal] += 1


def _dedupe(values: Any) -> list[Any]:
    seen = set()
    out = []
    for value in values or []:
        key = json.dumps(value, sort_keys=True, default=str) if isinstance(value, dict) else str(value)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _load_jsonl(path: Path, limit: int = 200) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except Exception:
                continue
            if isinstance(data, dict):
                rows.append(data)
    except Exception:
        return []
    return rows


def _append_jsonl(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = [
    "simulate_file_self_learning",
    "simulate_file_learning_mode",
    "record_file_learning_outcome",
]
