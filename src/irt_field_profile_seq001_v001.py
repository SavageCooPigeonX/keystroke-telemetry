"""Deterministic transcript replay for IRT artifact-probe intent keys.

V1 keeps IRT first: each artifact/chunk emits implied trajectory keys, the
profile resolves them against monthly and active priors, then drift decides
whether the profile reinforces, extends, mutates, probes, or recalculates MFS
(Model Favorability Score).
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.tc_semantic_profile_seq001_v001 import classify_semantic_intents, load_profile

SCHEMA = "irt_field_profile/v1"
DEFAULT_START = datetime(2026, 1, 1, tzinfo=timezone.utc)

THEME_WORDS = {
    "ai_modeling": {"ai", "model", "models", "neural", "training", "compute", "inference", "grok", "openai"},
    "field_sensing": {"microphone", "audio", "listen", "speech", "podcast", "whisper", "field", "hush", "pulse", "irt"},
    "engineering": {"build", "building", "engineer", "factory", "robot", "software", "system", "architecture"},
    "space": {"space", "rocket", "mars", "starship", "spacex", "orbit"},
    "vehicle_energy": {"tesla", "vehicle", "vehicles", "battery", "energy", "autonomy", "autopilot", "car", "cars"},
    "business_strategy": {"company", "market", "product", "cost", "strategy", "customers", "competition"},
    "risk_governance": {"risk", "safety", "regulation", "government", "policy", "control", "alignment", "trust"},
}
INTENT_KEY_PATTERNS = {
    "legacy_continuity": ({"legacy", "standard", "husband", "mission", "carry", "carrying", "honor"}, "implies continuity through inherited legacy, standard, or mission"),
    "leadership_legitimacy": ({"leader", "leadership", "ceo", "standard", "qualified", "authority", "legitimate"}, "implies authority, legitimacy, or right to lead"),
    "base_consolidation": ({"base", "supporters", "movement", "loyal", "loyalty", "rally", "together"}, "implies consolidating supporters around a shared direction"),
    "criticism_deflection": ({"critics", "criticism", "attack", "attacks", "defend", "deflect", "smear"}, "implies deflecting or reframing criticism"),
    "operational_independence": ({"independent", "independence", "operation", "operations", "strategy", "board", "execute"}, "implies independent operational control or strategic execution"),
    "ai_modeling": (THEME_WORDS["ai_modeling"], "implies continued emphasis on AI models, compute, or training direction"),
    "vehicle_autonomy": ({"tesla", "vehicle", "vehicles", "autonomy", "autopilot", "car", "cars"}, "implies continued emphasis on vehicle autonomy or Tesla execution"),
    "risk_governance": (THEME_WORDS["risk_governance"], "implies risk, safety, policy, or governance pressure"),
    "field_sensing": (THEME_WORDS["field_sensing"], "implies live field sensing, listening, Hush, or IRT probe work"),
}
KEY_ADJACENCY = {
    "legacy_continuity": {"leadership_legitimacy", "base_consolidation"},
    "leadership_legitimacy": {"legacy_continuity", "base_consolidation"},
    "ai_modeling": {"vehicle_autonomy"},
    "vehicle_autonomy": {"ai_modeling"},
    "risk_governance": {"criticism_deflection"},
}
KEY_CONFLICTS = {
    "legacy_continuity": {"operational_independence"},
    "operational_independence": {"legacy_continuity"},
    "leadership_legitimacy": {"criticism_deflection"},
    "ai_modeling": {"risk_governance"},
    "risk_governance": {"ai_modeling", "vehicle_autonomy"},
}
ENTITY_HINTS = {"Tesla": "organization", "SpaceX": "organization", "OpenAI": "organization", "xAI": "organization", "Twitter": "organization", "Starship": "product", "Mars": "place", "Elon Musk": "person"}
ENTITY_STOP = {"The", "This", "That", "There", "When", "Where", "Because", "And", "But", "So", "Then", "They", "We", "You", "He", "She", "It", "What", "Podcast", "Transcript"}
PRONOUNS = {"he", "she", "they", "it", "them", "him", "her", "that", "this"}
DRIFT_WORDS = {"but", "however", "actually", "instead", "unrelated", "different", "switch", "switched"}


def build_irt_profile(root: Path, run_id: str, source_meta: dict[str, Any]) -> dict[str, Any]:
    label = str(source_meta.get("label") or source_meta.get("source_label") or run_id)
    now = _utc_now()
    return {
        "schema": SCHEMA,
        "profile_id": "irt-profile-" + _hash(f"{run_id}|{label}")[:16],
        "run_id": run_id,
        "source_label": label,
        "mode": "transcript_replay",
        "created_at": now,
        "updated_at": now,
        "source_meta": dict(source_meta),
        "listen_state": "listening",
        "chunk_window": {},
        "entities": {},
        "intent_nodes": {},
        "artifact_probe_state": _new_probe_state(source_meta),
        "hush_pulses": [],
        "void_probes": [],
        "metrics": {"chunks_processed": 0, "graph_stability": 0.0, "entity_stability": 0.0, "context_churn": 0.0, "unknown_rate": 0.0, "probe_rate": 0.0, "resolution_entropy": 0.0, "drift_rate": 0.0, "mfs_trigger_rate": 0.0},
        "_runtime": {"unknown_chunks": 0, "drift_chunks": 0, "previous_selected_context": [], "maif_baselines": _load_maif_baselines(Path(root))},
    }


def chunk_transcript(text: str, chunk_seconds: int = 30, words_per_minute: int = 150, start_ts: str | None = None) -> list[dict[str, Any]]:
    words = re.findall(r"\S+", str(text or ""))
    if not words:
        return []
    seconds = max(1, int(chunk_seconds or 30))
    max_words = max(1, int(round((seconds / 60) * max(1, int(words_per_minute or 150)))))
    start = _parse_ts(start_ts) if start_ts else DEFAULT_START
    chunks = []
    for index, offset in enumerate(range(0, len(words), max_words), 1):
        chunk_start = start + timedelta(seconds=(index - 1) * seconds)
        chunks.append({
            "schema": "irt_speech_chunk/v1",
            "chunk_id": f"chunk-{index:04d}",
            "index": index,
            "start_seconds": (index - 1) * seconds,
            "end_seconds": index * seconds,
            "start_ts": chunk_start.isoformat(),
            "end_ts": (chunk_start + timedelta(seconds=seconds)).isoformat(),
            "text": " ".join(words[offset: offset + max_words]),
            "word_count": len(words[offset: offset + max_words]),
        })
    return chunks


def process_speech_chunk(root: Path, profile: dict[str, Any], chunk: dict[str, Any]) -> dict[str, Any]:
    text = str(chunk.get("text") or "")
    semantic = classify_semantic_intents(text, load_profile(Path(root)))
    entities = select_entity_profiles(profile, chunk)
    themes = _classify_themes(text, semantic)
    probe = probe_artifact_for_intent_keys(Path(root), profile, {**chunk, "entities": entities, "themes": themes, "semantic": semantic})
    resolved = resolve_intent_keys_against_profile(profile, probe["candidate_intent_keys"])
    mfs = should_run_mfs(profile, probe["artifact"], resolved["resolved_intent_keys"])
    applied = apply_intent_resolutions(profile, {**resolved, "artifact": probe["artifact"], "candidate_intent_keys": probe["candidate_intent_keys"], "mfs": mfs})
    selected, deranked, confidence = _update_intent_nodes(profile, chunk, entities, themes)
    confidence = max(confidence, float(applied.get("top_confidence") or 0.0))
    pulse = emit_hush_pulse(profile, chunk, entities, {"semantic": semantic, "themes": themes, "selected_context": selected, "deranked_context": deranked, "confidence": confidence, "artifact_probe": applied})
    _maybe_void_probe(profile, chunk, entities, themes, confidence, applied)
    _update_chunk_window(profile, chunk, themes, entities, selected, applied)
    _update_metrics(profile, semantic, themes, selected, applied)
    profile["updated_at"] = _utc_now()
    return pulse


def analyze_transcription_against_profile(root: Path, profile: dict[str, Any], transcript_text: str, chunk_seconds: int = 30, words_per_minute: int = 150) -> dict[str, Any]:
    for chunk in chunk_transcript(transcript_text, chunk_seconds, words_per_minute):
        process_speech_chunk(root, profile, chunk)
    return profile


def probe_artifact_for_intent_keys(root: Path, profile: dict[str, Any], artifact: dict[str, Any]) -> dict[str, Any]:
    entities = [item.get("canonical", str(item)) if isinstance(item, dict) else str(item) for item in artifact.get("entities") or []]
    artifact_id = str(artifact.get("chunk_id") or artifact.get("artifact_id") or f"artifact-{artifact.get('index', 0)}")
    normalized = {
        "artifact_id": artifact_id,
        "chunk_id": artifact.get("chunk_id", artifact_id),
        "chunk_index": int(artifact.get("index") or artifact.get("chunk_index") or 0),
        "text": str(artifact.get("text") or ""),
        "entities": entities,
        "themes": list(artifact.get("themes") or []),
        "semantic": artifact.get("semantic") if isinstance(artifact.get("semantic"), dict) else {},
        "timestamp": artifact.get("start_ts") or artifact.get("ts") or _utc_now(),
    }
    return {"schema": "artifact_intent_probe/v1", "artifact": normalized, "candidate_intent_keys": _extract_candidate_keys(normalized)}


def resolve_intent_keys_against_profile(profile: dict[str, Any], candidate_keys: list[dict[str, Any]]) -> dict[str, Any]:
    state = profile.setdefault("artifact_probe_state", _new_probe_state(profile.get("source_meta") or {}))
    active = state.setdefault("active_intent_keys", {})
    monthly = state.setdefault("monthly_intent_prior", {})
    items = []
    for candidate in candidate_keys:
        key = str(candidate.get("key") or "unknown_intent")
        prior_fit = max(float((active.get(key) or {}).get("confidence") or 0.0), float(monthly.get(key, 0.0)), _adjacent_fit(key, active))
        evidence = _prob(candidate.get("confidence", 0.0), 0.0)
        contradiction = _contradiction(key, active)
        posterior = max(0.0, min(1.0, prior_fit * 0.45 + evidence * 0.55 - contradiction * 0.35))
        drift = max(0.0, min(1.0, evidence * (1 - prior_fit) + contradiction * 0.7))
        resolution = _resolution(prior_fit, evidence, drift, contradiction)
        items.append({"key": key, "implied_trajectory": candidate.get("implied_trajectory", ""), "prior_fit": round(prior_fit, 4), "evidence_likelihood": round(evidence, 4), "posterior_fit": round(posterior, 4), "drift_score": round(drift, 4), "resolution": resolution, "reinforcement_delta": round(max(0.0, posterior - prior_fit), 4), "contradiction_delta": round(contradiction, 4), "probe_needed": resolution == "probe", "mfs_needed": resolution == "mfs", "candidate": candidate})
    return {"schema": "intent_key_resolution/v1", "resolved_intent_keys": items}


def apply_intent_resolutions(profile: dict[str, Any], resolution_pack: dict[str, Any]) -> dict[str, Any]:
    state = profile.setdefault("artifact_probe_state", _new_probe_state(profile.get("source_meta") or {}))
    artifact = resolution_pack.get("artifact") if isinstance(resolution_pack.get("artifact"), dict) else {}
    candidates = list(resolution_pack.get("candidate_intent_keys") or [])
    resolutions = list(resolution_pack.get("resolved_intent_keys") or [])
    mfs = resolution_pack.get("mfs") if isinstance(resolution_pack.get("mfs"), dict) else {}
    bindings = []
    for resolved in resolutions:
        candidate = resolved.get("candidate") if isinstance(resolved.get("candidate"), dict) else {}
        binding = {"artifact_id": artifact.get("artifact_id", candidate.get("source_artifact_id", "")), "entity": candidate.get("entity", ""), "candidate_key": candidate.get("key", resolved.get("key", "")), "resolved_key": resolved.get("key", ""), "resolution": resolved.get("resolution", ""), "confidence": resolved.get("evidence_likelihood", 0.0), "drift_score": resolved.get("drift_score", 0.0), "timestamp": artifact.get("timestamp") or _utc_now()}
        bindings.append(binding)
        if resolved.get("resolution") in {"reinforce", "extend", "mutate"}:
            _active_key_update(state, resolved, candidate, binding)
        if float(resolved.get("drift_score") or 0.0) >= 0.45:
            state.setdefault("drift_events", []).append({**binding, "reason": resolved.get("resolution"), "contradiction_delta": resolved.get("contradiction_delta", 0.0)})
        if resolved.get("probe_needed"):
            state.setdefault("probe_requests", []).append({**binding, "question": _probe_question("intent_key_resolution", str(resolved.get("key") or ""))})
    if mfs.get("mfs_needed"):
        state.setdefault("mfs_requests", []).append(mfs)
    state["artifact_bindings"] = _last([*state.get("artifact_bindings", []), *bindings], 200)
    state["candidate_intent_keys"] = candidates
    state["resolved_intent_keys"] = resolutions
    state["latest_resolution"] = {"artifact": artifact, "candidate_intent_keys": candidates, "resolved_intent_keys": resolutions, "artifact_bindings": bindings, "mfs": mfs}
    state["updated_at"] = _utc_now()
    top = max(resolutions, key=lambda item: float(item.get("posterior_fit") or 0.0), default={})
    return {"schema": "artifact_probe_resolution_applied/v1", **state["latest_resolution"], "top_key": top.get("key", ""), "top_confidence": top.get("posterior_fit", 0.0), "max_drift_score": max([float(item.get("drift_score") or 0.0) for item in resolutions] or [0.0]), "has_probe": any(item.get("probe_needed") for item in resolutions), "has_mfs": bool(mfs.get("mfs_needed"))}


def should_run_mfs(profile: dict[str, Any], artifact: dict[str, Any], resolutions: list[dict[str, Any]]) -> dict[str, Any]:
    if not resolutions:
        return {"mfs_needed": False, "reason": "no_resolutions", "model_favorability_score_delta": 0.0}
    max_drift = max(float(item.get("drift_score") or 0.0) for item in resolutions)
    max_conf = max(float(item.get("evidence_likelihood") or 0.0) for item in resolutions)
    contradiction = max(float(item.get("contradiction_delta") or 0.0) for item in resolutions)
    needed = (max_drift >= 0.62 and max_conf >= 0.62) or contradiction >= 0.55
    delta = round(min(1.0, max_drift * 0.65 + contradiction * 0.35), 4)
    return {"schema": "model_favorability_score_trigger/v1", "artifact_id": artifact.get("artifact_id", ""), "mfs_needed": bool(needed), "model_favorability_score_delta": delta if needed else 0.0, "reason": "high_drift_model_favorability_recalc" if needed else "normal_resolution", "max_drift_score": round(max_drift, 4), "max_confidence": round(max_conf, 4), "max_contradiction_delta": round(contradiction, 4)}


def select_entity_profiles(profile: dict[str, Any], chunk: dict[str, Any]) -> list[dict[str, Any]]:
    text = str(chunk.get("text") or "")
    found = _extract_entities(text)
    if not found and re.search(r"\bMusk\b", text) and "elon_musk" in profile.get("entities", {}):
        found = ["Elon Musk"]
    selected = []
    entities = profile.setdefault("entities", {})
    for raw in found:
        key = _entity_key(_resolve_entity(entities, raw))
        canonical = _resolve_entity(entities, raw)
        entry = entities.setdefault(key, {"canonical": canonical, "aliases": [], "type": ENTITY_HINTS.get(canonical, "unknown"), "confidence": 0.0, "support_count": 0, "first_seen": chunk.get("index", 0), "last_seen": chunk.get("index", 0), "evidence_snippets": [], "maif_baseline_matches": _maif_matches(profile, canonical)})
        if raw != canonical and raw not in entry["aliases"]:
            entry["aliases"].append(raw)
        entry["support_count"] = int(entry.get("support_count") or 0) + 1
        entry["last_seen"] = chunk.get("index", 0)
        entry["confidence"] = round(min(0.99, 0.32 + entry["support_count"] * 0.18), 4)
        entry["evidence_snippets"] = _last([*entry.get("evidence_snippets", []), _snippet(text, raw)], 5)
        selected.append(dict(entry))
    return selected


def emit_hush_pulse(profile: dict[str, Any], chunk: dict[str, Any], entities: list[dict[str, Any]], intents: dict[str, Any]) -> dict[str, Any]:
    trigger, state, reason = _hush_trigger(profile, chunk, entities, intents)
    pulse = {"schema": "irt_hush_pulse/v1", "chunk_id": chunk.get("chunk_id"), "chunk_index": int(chunk.get("index") or 0), "trigger": trigger, "listen_state": state, "withheld_context": [], "selected_context": intents.get("selected_context", []), "deranked_context": intents.get("deranked_context", []), "reason": reason}
    if state in {"hush", "probe"}:
        pulse["withheld_context"] = _last(intents.get("deranked_context", []), 6)
    profile["listen_state"] = state
    profile.setdefault("hush_pulses", []).append(pulse)
    return pulse


def render_field_report(profile: dict[str, Any]) -> str:
    lines = [f"# IRT Field Profile Report: {profile.get('source_label', '')}", "", f"- mode: `{profile.get('mode')}`", f"- listen_state: `{profile.get('listen_state')}`", f"- chunks_processed: `{profile.get('metrics', {}).get('chunks_processed', 0)}`", f"- graph_stability: `{profile.get('metrics', {}).get('graph_stability', 0)}`", "", "## Entities"]
    for entity in profile.get("entities", {}).values():
        lines.append(f"- {entity.get('canonical')} ({entity.get('type')}): confidence `{entity.get('confidence')}`, support `{entity.get('support_count')}`")
    lines += ["", "## Intent Nodes"]
    for node in profile.get("intent_nodes", {}).values():
        lines.append(f"- {node.get('theme')}: confidence `{node.get('confidence')}`, support `{node.get('support_count')}`, drift `{node.get('drift_score')}`")
    latest = profile.get("artifact_probe_state", {}).get("latest_resolution", {})
    if latest:
        mfs = latest.get("mfs") or {}
        lines += ["", "## Artifact Probe", f"- candidate_keys: `{len(latest.get('candidate_intent_keys') or [])}`", f"- resolved_keys: `{len(latest.get('resolved_intent_keys') or [])}`", f"- artifact_bindings: `{len(latest.get('artifact_bindings') or [])}`", f"- mfs_needed: `{mfs.get('mfs_needed', False)}`", f"- mfs_delta: `{mfs.get('model_favorability_score_delta', 0)}`"]
    return "\n".join(lines) + "\n"


def update_bayesian_intent_state(profile: dict[str, Any], chunk: dict[str, Any], entities: list[dict[str, Any]], themes: list[str], semantic: dict[str, Any]) -> dict[str, Any]:
    """Compatibility shim: current v1 resolves intent through artifact keys."""
    artifact = probe_artifact_for_intent_keys(Path("."), profile, {**chunk, "entities": entities, "themes": themes, "semantic": semantic})
    resolved = resolve_intent_keys_against_profile(profile, artifact["candidate_intent_keys"])
    return {"schema": "artifact_probe_state_shim/v1", "chunk_id": chunk.get("chunk_id"), **resolved}


def _new_probe_state(source_meta: dict[str, Any]) -> dict[str, Any]:
    monthly = source_meta.get("monthly_intent_prior") if isinstance(source_meta, dict) else None
    return {"schema": "artifact_probe_intent_resolution/v1", "monthly_intent_prior": dict(monthly) if isinstance(monthly, dict) else {}, "active_intent_keys": {}, "candidate_intent_keys": [], "resolved_intent_keys": [], "artifact_bindings": [], "drift_events": [], "mfs_requests": [], "probe_requests": [], "latest_resolution": {}, "updated_at": _utc_now()}


def _extract_candidate_keys(artifact: dict[str, Any]) -> list[dict[str, Any]]:
    toks = set(_tokens(artifact.get("text") or ""))
    entity = next((item for item in artifact.get("entities") or [] if item), "unknown_entity")
    candidates = []
    for key, (terms, trajectory) in INTENT_KEY_PATTERNS.items():
        hits = sorted(toks & set(terms))
        if hits:
            conf = min(0.96, 0.34 + len(hits) * 0.12 + (0.08 if entity != "unknown_entity" else 0.0))
            candidates.append({"key": key, "implied_trajectory": trajectory, "evidence": hits[:12], "confidence": round(conf, 4), "entity": entity, "source_artifact_id": artifact.get("artifact_id", ""), "temporal_context": {"chunk_index": artifact.get("chunk_index", 0), "timestamp": artifact.get("timestamp", "")}})
    if not candidates:
        candidates.append({"key": "unknown_intent", "implied_trajectory": "artifact evidence did not expose a stable implied trajectory", "evidence": _tokens(artifact.get("text") or "")[:8], "confidence": 0.22, "entity": entity, "source_artifact_id": artifact.get("artifact_id", ""), "temporal_context": {"chunk_index": artifact.get("chunk_index", 0), "timestamp": artifact.get("timestamp", "")}})
    return sorted(candidates, key=lambda item: (float(item["confidence"]), item["key"]), reverse=True)[:6]


def _adjacent_fit(key: str, active: dict[str, Any]) -> float:
    return max([float((active.get(rel) or {}).get("confidence") or 0.0) * 0.62 for rel in KEY_ADJACENCY.get(key, set())] or [0.0])


def _contradiction(key: str, active: dict[str, Any]) -> float:
    return max([float((active.get(conflict) or {}).get("confidence") or 0.0) for conflict in KEY_CONFLICTS.get(key, set())] or [0.0])


def _resolution(prior_fit: float, evidence: float, drift: float, contradiction: float) -> str:
    if evidence < 0.34:
        return "probe"
    if contradiction >= 0.55:
        return "contradict"
    if drift >= 0.72 and evidence >= 0.62:
        return "mfs"
    if drift >= 0.5:
        return "mutate"
    if prior_fit >= 0.58:
        return "reinforce"
    return "extend" if prior_fit >= 0.22 or evidence >= 0.52 else "probe"


def _active_key_update(state: dict[str, Any], resolved: dict[str, Any], candidate: dict[str, Any], binding: dict[str, Any]) -> None:
    active = state.setdefault("active_intent_keys", {})
    key = str(resolved.get("key") or "")
    prior = active.get(key, {})
    support = int(prior.get("support_count") or 0) + 1
    confidence = max(float(prior.get("confidence") or 0.0) * 0.72, float(resolved.get("posterior_fit") or 0.0))
    active[key] = {"key": key, "implied_trajectory": candidate.get("implied_trajectory", prior.get("implied_trajectory", "")), "confidence": round(min(0.99, confidence + min(0.18, support * 0.025)), 4), "support_count": support, "last_resolution": resolved.get("resolution", ""), "last_artifact_id": binding.get("artifact_id", ""), "last_seen": binding.get("timestamp", ""), "evidence": _last([*(prior.get("evidence") or []), *(candidate.get("evidence") or [])], 12)}


def _update_intent_nodes(profile: dict[str, Any], chunk: dict[str, Any], entities: list[dict[str, Any]], themes: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], float]:
    nodes = profile.setdefault("intent_nodes", {})
    index = int(chunk.get("index") or 0)
    text = str(chunk.get("text") or "")
    entity_names = [item["canonical"] for item in entities]
    selected = []
    for theme in themes or ["unknown"]:
        node = nodes.setdefault(theme, {"node_id": "irt-node-" + _hash(theme)[:16], "theme": theme, "entities": [], "confidence": 0.0, "support_count": 0, "drift_score": 0.0, "context_score": 0.0, "first_seen": index, "last_seen": index, "evidence_snippets": [], "score_parts": {}})
        previous = set(node.get("entities") or [])
        for name in entity_names:
            if name not in node["entities"]:
                node["entities"].append(name)
        support = int(node.get("support_count") or 0) + 1
        gap = max(0, index - int(node.get("last_seen") or index))
        drift = _drift_penalty(text, gap, entity_names, previous)
        continuity = 1.0 if gap <= 1 else max(0.0, 1 - gap * 0.12)
        recurrence = min(1.0, (len(previous & set(entity_names)) + max(0, support - 1)) / 4.0)
        context = max(0.0, min(1.0, 0.34 + 0.26 * recurrence + 0.2 * continuity + 0.12 * _maif_theme_similarity(profile, theme, entity_names) - 0.18 * drift))
        node.update({"support_count": support, "last_seen": index, "confidence": round(min(0.99, 0.25 + support * 0.15 + context * 0.35), 4), "drift_score": round(drift, 4), "context_score": round(context, 4), "evidence_snippets": _last([*node.get("evidence_snippets", []), text[:180]], 5), "score_parts": {"theme_overlap": 1.0, "entity_recurrence": round(recurrence, 4), "temporal_continuity": round(continuity, 4), "maif_baseline_similarity": round(_maif_theme_similarity(profile, theme, entity_names), 4), "contradiction_drift_penalty": round(drift, 4), "stale_context_penalty": 0.0}})
        selected.append({"node_id": node["node_id"], "theme": theme, "context_score": node["context_score"], "confidence": node["confidence"], "entities": node["entities"][:6]})
    selected.sort(key=lambda item: (item["context_score"], item["confidence"]), reverse=True)
    selected_ids = {item["node_id"] for item in selected[:4]}
    deranked = [{"node_id": n.get("node_id"), "theme": n.get("theme"), "context_score": n.get("context_score", 0), "reason": "stale_or_weak_context"} for n in nodes.values() if n.get("node_id") not in selected_ids and float(n.get("context_score") or 0) < 0.42]
    return selected[:4], deranked[:8], float(selected[0]["confidence"] if selected else 0.0)


def _maybe_void_probe(profile: dict[str, Any], chunk: dict[str, Any], entities: list[dict[str, Any]], themes: list[str], confidence: float, applied: dict[str, Any]) -> None:
    toks = set(_tokens(chunk.get("text") or ""))
    ambiguous = bool(toks & PRONOUNS) and not entities
    max_drift = float(applied.get("max_drift_score") or 0.0)
    if confidence >= 0.42 and not ambiguous and themes != ["unknown"] and max_drift < 0.5 and not applied.get("has_probe") and not applied.get("has_mfs"):
        return
    reason = "missing_entity_reference" if ambiguous else "model_favorability_score" if applied.get("has_mfs") else "intent_key_resolution" if applied.get("has_probe") else "profile_drift" if max_drift >= 0.5 else "low_confidence_or_unknown_theme"
    target = str(applied.get("top_key") or (themes[0] if themes else "unknown_intent"))
    profile.setdefault("void_probes", []).append({"question": _probe_question(reason, target), "target_entity_or_intent": target, "reason": reason, "confidence_before": round(confidence, 4), "confidence_after": round(max(confidence, 0.42), 4), "chunk_id": chunk.get("chunk_id"), "chunk_index": int(chunk.get("index") or 0)})


def _update_chunk_window(profile: dict[str, Any], chunk: dict[str, Any], themes: list[str], entities: list[dict[str, Any]], selected: list[dict[str, Any]], applied: dict[str, Any]) -> None:
    bits = list((profile.get("chunk_window") or {}).get("rolling_summary_bits") or [])
    names = [item["canonical"] for item in entities[:4]]
    bits.append(f"{chunk.get('chunk_id')}: {', '.join(themes[:2]) or 'unknown'} / {', '.join(names) or 'no entity'}")
    profile["chunk_window"] = {"chunk_id": chunk.get("chunk_id"), "index": int(chunk.get("index") or 0), "start_ts": chunk.get("start_ts"), "end_ts": chunk.get("end_ts"), "text": str(chunk.get("text") or "")[:500], "themes": themes, "entities": names, "selected_context": selected, "candidate_intent_keys": applied.get("candidate_intent_keys", []), "resolved_intent_keys": applied.get("resolved_intent_keys", []), "top_key": applied.get("top_key", ""), "rolling_summary": " | ".join(bits[-8:]), "rolling_summary_bits": bits[-8:]}


def _update_metrics(profile: dict[str, Any], semantic: dict[str, Any], themes: list[str], selected: list[dict[str, Any]], applied: dict[str, Any]) -> None:
    metrics, runtime = profile.setdefault("metrics", {}), profile.setdefault("_runtime", {})
    processed = int(metrics.get("chunks_processed") or 0) + 1
    metrics["chunks_processed"] = processed
    if semantic.get("semantic_intent") == "unknown" and themes == ["unknown"]:
        runtime["unknown_chunks"] = int(runtime.get("unknown_chunks") or 0) + 1
    if float(applied.get("max_drift_score") or 0.0) >= 0.5:
        runtime["drift_chunks"] = int(runtime.get("drift_chunks") or 0) + 1
    selected_keys = [str(item.get("node_id")) for item in selected]
    previous = list(runtime.get("previous_selected_context") or [])
    runtime["previous_selected_context"] = selected_keys
    metrics.update({"context_churn": round(_churn(previous, selected_keys), 4), "graph_stability": round(_support_stability(list(profile.get("intent_nodes", {}).values())), 4), "entity_stability": round(_support_stability(list(profile.get("entities", {}).values())), 4), "unknown_rate": round(int(runtime.get("unknown_chunks") or 0) / max(1, processed), 4), "probe_rate": round(len(profile.get("void_probes") or []) / max(1, processed), 4), "resolution_entropy": round(_resolution_entropy(applied.get("resolved_intent_keys", [])), 4), "drift_rate": round(int(runtime.get("drift_chunks") or 0) / max(1, processed), 4), "mfs_trigger_rate": round(len((profile.get("artifact_probe_state") or {}).get("mfs_requests", [])) / max(1, processed), 4)})


def _classify_themes(text: str, semantic: dict[str, Any]) -> list[str]:
    toks = set(_tokens(text))
    scored = [(theme, len(toks & words)) for theme, words in THEME_WORDS.items() if toks & words]
    if "live_field_intent_modeling" in (semantic.get("semantic_intents") or []):
        scored.append(("field_sensing", 2))
    if not scored:
        return ["unknown"]
    return [theme for theme, _hits in sorted(scored, key=lambda pair: (-pair[1], pair[0]))[:3]]


def _extract_entities(text: str) -> list[str]:
    found = [known for known in ENTITY_HINTS if re.search(rf"\b{re.escape(known)}\b", text, re.I)]
    for match in re.finditer(r"\b[A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*){0,3}\b", text):
        raw = match.group(0).strip()
        if raw not in ENTITY_STOP and raw.lower() not in {"ai", "irt"} and len(raw) >= 2:
            found.append(raw)
    result = []
    for item in found:
        if item not in result:
            result.append(item)
    return result[:8]


def _resolve_entity(entities: dict[str, Any], raw: str) -> str:
    if raw == "Musk" and "elon_musk" in entities:
        return "Elon Musk"
    for key, entry in entities.items():
        if raw == entry.get("canonical") or raw in entry.get("aliases", []):
            return str(entry.get("canonical"))
    return "Elon Musk" if raw == "Musk" else raw


def _hush_trigger(profile: dict[str, Any], chunk: dict[str, Any], entities: list[dict[str, Any]], intents: dict[str, Any]) -> tuple[str, str, str]:
    text = str(chunk.get("text") or "")
    themes = intents.get("themes") or []
    applied = intents.get("artifact_probe") or {}
    confidence = float(intents.get("confidence") or 0.0)
    if bool(set(_tokens(text)) & PRONOUNS) and not entities:
        return "missing_entity_reference", "probe", "ambiguous entity reference; create void probe"
    if applied.get("has_mfs"):
        return "model_favorability_score", "hush", "high drift requires MFS recalculation before profile commit"
    if themes == ["unknown"]:
        return "unknown_theme", "hush", "no stable theme; withhold weak context"
    if set(_tokens(text)) & DRIFT_WORDS or float(applied.get("max_drift_score") or 0.0) >= 0.5:
        return "topic_shift", "hush", "topic drift; do not commit weak resolution as stable truth"
    if applied.get("has_probe"):
        return "intent_key_probe", "probe", "intent key could not resolve confidently"
    if confidence < 0.38:
        return "low_confidence", "hush", "low-confidence context withheld"
    return "stable_context", "listening", "context selected"


def _load_maif_baselines(root: Path) -> list[dict[str, Any]]:
    baselines = []
    for path in (root / "logs").glob("repo_fingerprint_*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        baselines.append({"label": data.get("label", path.stem), "schema": data.get("schema", ""), "file_count": len(data.get("files") or [])})
    return baselines


def _maif_matches(profile: dict[str, Any], entity: str) -> list[dict[str, Any]]:
    return [{"label": item.get("label", ""), "match": "redacted_fingerprint", "confidence": 0.56} for item in profile.get("_runtime", {}).get("maif_baselines", [])[:3]]


def _maif_theme_similarity(profile: dict[str, Any], theme: str, entities: list[str]) -> float:
    return 0.18 if profile.get("_runtime", {}).get("maif_baselines") and (entities or theme != "unknown") else 0.0


def _drift_penalty(text: str, gap: int, entity_names: list[str], previous_entities: set[str]) -> float:
    penalty = 0.0
    if set(_tokens(text)) & DRIFT_WORDS:
        penalty += 0.45
    if previous_entities and entity_names and not previous_entities & set(entity_names):
        penalty += 0.24
    if gap > 3:
        penalty += min(0.25, gap * 0.04)
    return min(1.0, penalty)


def _support_stability(items: list[dict[str, Any]]) -> float:
    if not items:
        return 0.0
    return min(1.0, sum(min(1.0, float(item.get("support_count") or 0) / 3.0) for item in items) / len(items))


def _resolution_entropy(resolutions: list[dict[str, Any]]) -> float:
    if not resolutions:
        return 0.0
    unique = len({item.get("resolution") for item in resolutions})
    return min(1.0, unique / 6.0)


def _churn(previous: list[str], current: list[str]) -> float:
    if not previous and not current:
        return 0.0
    return 1.0 - (len(set(previous) & set(current)) / max(1, len(set(previous) | set(current))))


def _probe_question(reason: str, target: str) -> str:
    questions = {"missing_entity_reference": "Which entity owns this implied trajectory?", "model_favorability_score": "Should MFS be recalculated before this artifact changes the profile?", "intent_key_resolution": "What profile evidence resolves this implied intent key?", "profile_drift": "Is this drift a real direction change or a local artifact anomaly?"}
    return f"{questions.get(reason, 'What missing context would resolve this artifact?')} Target: {target}"


def _snippet(text: str, term: str, radius: int = 70) -> str:
    idx = text.lower().find(str(term).lower())
    if idx < 0:
        return text[: radius * 2]
    return text[max(0, idx - radius): idx + len(term) + radius].strip()


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9_]+", str(text or "").lower())


def _entity_key(text: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", str(text).lower())).strip("_") or "unknown"


def _prob(value: Any, default: float = 0.5) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def _hash(text: str) -> str:
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def _last(items: list[Any], limit: int) -> list[Any]:
    return list(items)[-limit:]


def _parse_ts(value: str) -> datetime:
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return DEFAULT_START


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()
