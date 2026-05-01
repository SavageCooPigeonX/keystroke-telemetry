"""IRT field profile for deterministic speech-transcript replay.

This is the v1 field simulator: transcript chunks stand in for live audio,
then the profile accumulates entities, intent nodes, Hush pulses, and void
probes without microphone, ASR, network, or LLM dependencies.
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
CHUNK_SCHEMA = "irt_speech_chunk/v1"
PULSE_SCHEMA = "irt_hush_pulse/v1"
DEFAULT_START = datetime(2026, 1, 1, tzinfo=timezone.utc)

THEME_WORDS = {
    "ai_modeling": {
        "ai", "model", "models", "neural", "training", "intelligence",
        "agent", "agents", "compute", "inference", "grok", "openai",
    },
    "field_sensing": {
        "microphone", "microphones", "audio", "listen", "listening", "speech",
        "podcast", "voice", "whisper", "field", "hush", "pulse", "irt",
    },
    "engineering": {
        "build", "building", "engineer", "engineering", "factory", "robot",
        "manufacturing", "software", "system", "systems", "architecture",
    },
    "space": {"space", "rocket", "rockets", "mars", "starship", "spacex", "orbit"},
    "vehicle_energy": {
        "tesla", "car", "cars", "vehicle", "vehicles", "battery", "energy",
        "charging", "autonomy", "autopilot", "electric",
    },
    "business_strategy": {
        "company", "companies", "market", "product", "cost", "price", "margin",
        "strategy", "customers", "competition",
    },
    "risk_governance": {
        "risk", "safety", "regulation", "government", "policy", "control",
        "danger", "alignment", "truth", "trust",
    },
}
ENTITY_HINTS = {
    "Tesla": "organization",
    "SpaceX": "organization",
    "OpenAI": "organization",
    "xAI": "organization",
    "Twitter": "organization",
    "X": "organization",
    "Starship": "product",
    "Mars": "place",
    "Elon Musk": "person",
}
ENTITY_STOP = {
    "The", "This", "That", "There", "When", "Where", "Because", "And", "But",
    "So", "Then", "They", "We", "You", "I", "He", "She", "It", "What",
    "Podcast", "Transcript",
}
PRONOUNS = {"he", "she", "they", "it", "them", "him", "her", "that", "this"}
DRIFT_WORDS = {"but", "however", "actually", "instead", "unrelated", "different", "switch"}
INTENT_KEY_PATTERNS = {
    "legacy_continuity": {
        "terms": {"legacy", "standard", "husband", "mission", "carry", "carrying", "honor"},
        "trajectory": "implies continuity through inherited legacy, standard, or mission",
    },
    "leadership_legitimacy": {
        "terms": {"leader", "leadership", "ceo", "standard", "qualified", "authority", "legitimate"},
        "trajectory": "implies authority, legitimacy, or right to lead",
    },
    "base_consolidation": {
        "terms": {"base", "supporters", "movement", "loyal", "loyalty", "rally", "together"},
        "trajectory": "implies consolidating supporters around a shared direction",
    },
    "criticism_deflection": {
        "terms": {"critics", "criticism", "attack", "attacks", "defend", "deflect", "smear"},
        "trajectory": "implies deflecting or reframing criticism",
    },
    "operational_independence": {
        "terms": {"independent", "independence", "operation", "operations", "strategy", "board", "execute"},
        "trajectory": "implies independent operational control or strategic execution",
    },
    "ai_modeling": {
        "terms": THEME_WORDS["ai_modeling"],
        "trajectory": "implies continued emphasis on AI models, compute, or training direction",
    },
    "vehicle_autonomy": {
        "terms": {"tesla", "vehicle", "vehicles", "autonomy", "autopilot", "car", "cars"},
        "trajectory": "implies continued emphasis on vehicle autonomy or Tesla execution",
    },
    "risk_governance": {
        "terms": THEME_WORDS["risk_governance"],
        "trajectory": "implies risk, safety, policy, or governance pressure",
    },
    "field_sensing": {
        "terms": THEME_WORDS["field_sensing"],
        "trajectory": "implies live field sensing, listening, Hush, or IRT probe work",
    },
}
INTENT_KEY_CONFLICTS = {
    "legacy_continuity": {"operational_independence"},
    "leadership_legitimacy": {"criticism_deflection"},
    "operational_independence": {"legacy_continuity"},
    "ai_modeling": {"risk_governance"},
    "risk_governance": {"ai_modeling", "vehicle_autonomy"},
}
RESOLUTION_STATES = {"reinforce", "extend", "mutate", "contradict", "probe", "mfs"}


def build_irt_profile(root: Path, run_id: str, source_meta: dict[str, Any]) -> dict[str, Any]:
    """Create an empty live-field profile seeded with MAIF fingerprint metadata."""
    root = Path(root)
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
        "artifact_probe_state": _new_artifact_probe_state(source_meta),
        "hush_pulses": [],
        "void_probes": [],
        "metrics": {
            "chunks_processed": 0,
            "graph_stability": 0.0,
            "entity_stability": 0.0,
            "context_churn": 0.0,
            "unknown_rate": 0.0,
            "probe_rate": 0.0,
            "resolution_entropy": 0.0,
            "drift_rate": 0.0,
            "mfs_trigger_rate": 0.0,
        },
        "_runtime": {
            "unknown_chunks": 0,
            "drift_chunks": 0,
            "previous_selected_context": [],
            "maif_baselines": _load_maif_baselines(root),
        },
    }


def chunk_transcript(
    text: str,
    chunk_seconds: int = 30,
    words_per_minute: int = 150,
    start_ts: str | None = None,
) -> list[dict[str, Any]]:
    """Split transcript text into deterministic simulated-live chunks."""
    words = re.findall(r"\S+", str(text or ""))
    if not words:
        return []
    seconds = max(1, int(chunk_seconds or 30))
    max_words = max(1, int(round((seconds / 60.0) * max(1, words_per_minute))))
    start = _parse_ts(start_ts) if start_ts else DEFAULT_START
    chunks: list[dict[str, Any]] = []
    for index, offset in enumerate(range(0, len(words), max_words), 1):
        part = words[offset: offset + max_words]
        chunk_start = start + timedelta(seconds=(index - 1) * seconds)
        chunk_end = chunk_start + timedelta(seconds=seconds)
        chunks.append({
            "schema": CHUNK_SCHEMA,
            "chunk_id": f"chunk-{index:04d}",
            "index": index,
            "start_seconds": (index - 1) * seconds,
            "end_seconds": index * seconds,
            "start_ts": chunk_start.isoformat(),
            "end_ts": chunk_end.isoformat(),
            "text": " ".join(part),
            "word_count": len(part),
        })
    return chunks


def process_speech_chunk(root: Path, profile: dict[str, Any], chunk: dict[str, Any]) -> dict[str, Any]:
    """Mutate profile with one transcript chunk and return the emitted IRT pulse."""
    root = Path(root)
    text = str(chunk.get("text") or "")
    semantic = classify_semantic_intents(text, load_profile(root))
    entities = select_entity_profiles(profile, chunk)
    themes = _classify_themes(text, semantic)
    artifact_probe = probe_artifact_for_intent_keys(root, profile, {
        **chunk,
        "entities": entities,
        "themes": themes,
        "semantic": semantic,
    })
    resolution = resolve_intent_keys_against_profile(profile, artifact_probe["candidate_intent_keys"])
    mfs = should_run_mfs(profile, artifact_probe["artifact"], resolution["resolved_intent_keys"])
    applied = apply_intent_resolutions(profile, {
        **resolution,
        "artifact": artifact_probe["artifact"],
        "candidate_intent_keys": artifact_probe["candidate_intent_keys"],
        "mfs": mfs,
    })
    selected, deranked, confidence = _update_intent_nodes(profile, chunk, entities, themes)
    confidence = max(confidence, float(applied.get("top_confidence") or 0.0))
    pulse = emit_hush_pulse(
        profile,
        chunk,
        entities,
        {
            "semantic": semantic,
            "themes": themes,
            "selected_context": selected,
            "deranked_context": deranked,
            "confidence": confidence,
            "artifact_probe": applied,
        },
    )
    _maybe_emit_void_probe(profile, chunk, entities, themes, confidence, applied)
    _update_chunk_window(profile, chunk, themes, entities, selected, applied)
    _update_metrics(profile, semantic, themes, selected, applied)
    profile["updated_at"] = _utc_now()
    return pulse


def analyze_transcription_against_profile(
    root: Path,
    profile: dict[str, Any],
    transcript_text: str,
    chunk_seconds: int = 30,
    words_per_minute: int = 150,
) -> dict[str, Any]:
    """Replay transcript text through the live Bayesian profile state."""
    for chunk in chunk_transcript(
        transcript_text,
        chunk_seconds=chunk_seconds,
        words_per_minute=words_per_minute,
    ):
        process_speech_chunk(root, profile, chunk)
    return profile


def probe_artifact_for_intent_keys(root: Path, profile: dict[str, Any], artifact: dict[str, Any]) -> dict[str, Any]:
    """IRT-style probe: extract candidate implied-trajectory keys from artifact evidence."""
    text = str(artifact.get("text") or "")
    entities = list(artifact.get("entities") or [])
    themes = list(artifact.get("themes") or [])
    semantic = artifact.get("semantic") if isinstance(artifact.get("semantic"), dict) else {}
    source_artifact_id = str(artifact.get("chunk_id") or artifact.get("artifact_id") or f"artifact-{artifact.get('index', 0)}")
    normalized_artifact = {
        "artifact_id": source_artifact_id,
        "chunk_id": artifact.get("chunk_id", source_artifact_id),
        "chunk_index": int(artifact.get("index") or artifact.get("chunk_index") or 0),
        "text": text,
        "entities": [item.get("canonical", str(item)) if isinstance(item, dict) else str(item) for item in entities],
        "themes": themes,
        "semantic": semantic,
        "timestamp": artifact.get("start_ts") or artifact.get("ts") or _utc_now(),
    }
    candidate_keys = _extract_candidate_intent_keys(normalized_artifact)
    return {
        "schema": "artifact_intent_probe/v1",
        "artifact": normalized_artifact,
        "candidate_intent_keys": candidate_keys,
    }


def resolve_intent_keys_against_profile(
    profile: dict[str, Any],
    candidate_keys: list[dict[str, Any]],
) -> dict[str, Any]:
    """Resolve artifact-side candidate keys against monthly + active profile state."""
    state = profile.setdefault("artifact_probe_state", _new_artifact_probe_state(profile.get("source_meta") or {}))
    active = state.setdefault("active_intent_keys", {})
    monthly = state.setdefault("monthly_intent_prior", {})
    resolutions = []
    for candidate in candidate_keys:
        key = str(candidate.get("key") or "unknown_intent")
        active_entry = active.get(key, {})
        active_conf = float(active_entry.get("confidence") or 0.0)
        monthly_conf = float(monthly.get(key, 0.0))
        adjacent_fit = _adjacent_key_fit(key, active)
        prior_fit = max(active_conf, monthly_conf, adjacent_fit)
        evidence = _coerce_probability(candidate.get("confidence", 0.0), default=0.0)
        contradiction = _key_contradiction_delta(key, active)
        posterior_fit = max(0.0, min(1.0, (prior_fit * 0.45) + (evidence * 0.55) - (contradiction * 0.35)))
        drift_score = max(0.0, min(1.0, (evidence * (1.0 - prior_fit)) + contradiction * 0.7))
        resolution = _resolution_state(prior_fit, evidence, drift_score, contradiction)
        resolutions.append({
            "key": key,
            "implied_trajectory": candidate.get("implied_trajectory", ""),
            "prior_fit": round(prior_fit, 4),
            "evidence_likelihood": round(evidence, 4),
            "posterior_fit": round(posterior_fit, 4),
            "drift_score": round(drift_score, 4),
            "resolution": resolution,
            "reinforcement_delta": round(max(0.0, posterior_fit - prior_fit), 4),
            "contradiction_delta": round(contradiction, 4),
            "probe_needed": resolution == "probe",
            "mfs_needed": resolution == "mfs",
            "candidate": candidate,
        })
    return {
        "schema": "intent_key_resolution/v1",
        "resolved_intent_keys": resolutions,
    }


def apply_intent_resolutions(profile: dict[str, Any], resolution_pack: dict[str, Any]) -> dict[str, Any]:
    """Apply stable resolutions and preserve artifact binding receipts."""
    state = profile.setdefault("artifact_probe_state", _new_artifact_probe_state(profile.get("source_meta") or {}))
    artifact = resolution_pack.get("artifact") if isinstance(resolution_pack.get("artifact"), dict) else {}
    candidates = list(resolution_pack.get("candidate_intent_keys") or [])
    resolutions = list(resolution_pack.get("resolved_intent_keys") or [])
    mfs = resolution_pack.get("mfs") if isinstance(resolution_pack.get("mfs"), dict) else {}
    bindings = []
    for resolved in resolutions:
        candidate = resolved.get("candidate") if isinstance(resolved.get("candidate"), dict) else {}
        binding = {
            "artifact_id": artifact.get("artifact_id", candidate.get("source_artifact_id", "")),
            "entity": candidate.get("entity", ""),
            "candidate_key": candidate.get("key", resolved.get("key", "")),
            "resolved_key": resolved.get("key", ""),
            "resolution": resolved.get("resolution", ""),
            "confidence": resolved.get("evidence_likelihood", 0.0),
            "drift_score": resolved.get("drift_score", 0.0),
            "timestamp": artifact.get("timestamp") or _utc_now(),
        }
        bindings.append(binding)
        if resolved.get("resolution") in {"reinforce", "extend", "mutate"}:
            _apply_active_key_update(state, resolved, candidate, binding)
        if float(resolved.get("drift_score") or 0.0) >= 0.45:
            state.setdefault("drift_events", []).append({
                **binding,
                "reason": resolved.get("resolution"),
                "contradiction_delta": resolved.get("contradiction_delta", 0.0),
            })
        if resolved.get("probe_needed"):
            state.setdefault("probe_requests", []).append({
                **binding,
                "question": _probe_question("intent_key_resolution", str(resolved.get("key") or "")),
            })
    if mfs.get("mfs_needed"):
        state.setdefault("mfs_requests", []).append(mfs)
    state["artifact_bindings"] = _last_items([*state.get("artifact_bindings", []), *bindings], 200)
    state["candidate_intent_keys"] = candidates
    state["resolved_intent_keys"] = resolutions
    state["latest_resolution"] = {
        "artifact": artifact,
        "candidate_intent_keys": candidates,
        "resolved_intent_keys": resolutions,
        "artifact_bindings": bindings,
        "mfs": mfs,
    }
    state["updated_at"] = _utc_now()
    top = max(resolutions, key=lambda item: float(item.get("posterior_fit") or 0.0), default={})
    return {
        "schema": "artifact_probe_resolution_applied/v1",
        **state["latest_resolution"],
        "top_key": top.get("key", ""),
        "top_confidence": top.get("posterior_fit", 0.0),
        "max_drift_score": max([float(item.get("drift_score") or 0.0) for item in resolutions] or [0.0]),
        "has_probe": any(item.get("probe_needed") for item in resolutions),
        "has_mfs": bool(mfs.get("mfs_needed")),
    }


def should_run_mfs(
    profile: dict[str, Any],
    artifact: dict[str, Any],
    resolutions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Decide whether Model Favorability Score must be recalculated for this artifact."""
    if not resolutions:
        return {"mfs_needed": False, "reason": "no_resolutions", "model_favorability_score_delta": 0.0}
    max_drift = max(float(item.get("drift_score") or 0.0) for item in resolutions)
    max_conf = max(float(item.get("evidence_likelihood") or 0.0) for item in resolutions)
    contradiction = max(float(item.get("contradiction_delta") or 0.0) for item in resolutions)
    mfs_needed = (max_drift >= 0.62 and max_conf >= 0.62) or contradiction >= 0.55
    delta = round(min(1.0, (max_drift * 0.65) + (contradiction * 0.35)), 4)
    return {
        "schema": "model_favorability_score_trigger/v1",
        "artifact_id": artifact.get("artifact_id", ""),
        "mfs_needed": bool(mfs_needed),
        "model_favorability_score_delta": delta if mfs_needed else 0.0,
        "reason": "high_drift_model_favorability_recalc" if mfs_needed else "normal_resolution",
        "max_drift_score": round(max_drift, 4),
        "max_confidence": round(max_conf, 4),
        "max_contradiction_delta": round(contradiction, 4),
    }


def update_bayesian_intent_state(
    profile: dict[str, Any],
    chunk: dict[str, Any],
    entities: list[dict[str, Any]],
    themes: list[str],
    semantic: dict[str, Any],
) -> dict[str, Any]:
    """Update P(intent | transcript_chunk, profile_history)."""
    state = profile.setdefault("bayesian_intent_state", _new_bayesian_state(profile.get("source_meta") or {}))
    prior = _current_intent_prior(profile)
    likelihood = _evidence_likelihood(str(chunk.get("text") or ""), themes, semantic)
    coupled_prior, coupling_edges = _coupled_prior(profile, chunk, entities, themes, prior)
    coupling_strength = min(0.55, sum(float(edge.get("weight") or 0.0) for edge in coupling_edges))
    combined_prior = _blend_distributions(prior, coupled_prior, coupling_strength)
    posterior = _bayes_update(combined_prior, likelihood)
    standalone = _bayes_update(prior, likelihood)
    top_intent, top_confidence = _top_probability(posterior)
    entropy = _normalized_entropy(posterior)
    contradiction = _contradiction_pressure(coupling_edges, likelihood, posterior)
    confidence_inflation = _confidence_inflation(standalone, posterior)
    update = {
        "schema": "bayesian_intent_update/v1",
        "chunk_id": chunk.get("chunk_id"),
        "chunk_index": int(chunk.get("index") or 0),
        "source_reliability": _source_reliability(profile),
        "prior": prior,
        "evidence_likelihood": likelihood,
        "coupled_prior": coupled_prior,
        "coupling_strength": round(coupling_strength, 4),
        "coupling_edges": coupling_edges,
        "posterior": posterior,
        "standalone_posterior": standalone,
        "posterior_top": top_intent,
        "posterior_confidence": round(top_confidence, 4),
        "posterior_entropy": round(entropy, 4),
        "contradiction_score": round(contradiction, 4),
        "confidence_inflation": round(confidence_inflation, 4),
    }
    artifact = {
        "artifact_id": str(chunk.get("chunk_id") or f"chunk-{chunk.get('index', 0)}"),
        "chunk_index": update["chunk_index"],
        "text": str(chunk.get("text") or "")[:240],
        "tokens": _tokens(chunk.get("text") or ""),
        "themes": themes,
        "entities": [item["canonical"] for item in entities],
        "source_reliability": update["source_reliability"],
        "posterior": posterior,
        "posterior_top": top_intent,
        "posterior_confidence": update["posterior_confidence"],
    }
    state["prior"] = combined_prior
    state["posterior"] = posterior
    state["latest_update"] = update
    state["artifact_memory"] = _last_items([*state.get("artifact_memory", []), artifact], 24)
    state["coupling_edges"] = _last_items([*state.get("coupling_edges", []), *coupling_edges], 80)
    state["updated_at"] = _utc_now()
    return update


def select_entity_profiles(profile: dict[str, Any], chunk: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract and merge entity profiles from a speech chunk."""
    text = str(chunk.get("text") or "")
    index = int(chunk.get("index") or 0)
    entities = profile.setdefault("entities", {})
    found = _extract_entities(text)
    selected: list[dict[str, Any]] = []
    for raw in found:
        canonical = _resolve_entity(entities, raw)
        key = _entity_key(canonical)
        prior = entities.get(key)
        if not prior:
            prior = {
                "canonical": canonical,
                "aliases": [],
                "type": _entity_type(canonical),
                "confidence": 0.0,
                "support_count": 0,
                "first_seen": index,
                "last_seen": index,
                "evidence_snippets": [],
                "maif_baseline_matches": [],
            }
            entities[key] = prior
        if raw not in prior["aliases"]:
            prior["aliases"].append(raw)
        prior["support_count"] = int(prior.get("support_count") or 0) + 1
        prior["last_seen"] = index
        prior["confidence"] = round(min(0.99, 0.35 + int(prior["support_count"]) * 0.16), 4)
        prior["evidence_snippets"] = _last_items([
            *prior.get("evidence_snippets", []),
            _snippet(text, raw),
        ], 5)
        prior["maif_baseline_matches"] = _maif_matches(profile, canonical)
        selected.append(dict(prior))
    selected.sort(key=lambda item: (item["confidence"], item["support_count"], item["canonical"]), reverse=True)
    return selected


def emit_hush_pulse(
    profile: dict[str, Any],
    chunk: dict[str, Any],
    entities: list[dict[str, Any]],
    intents: dict[str, Any],
) -> dict[str, Any]:
    """Emit the Hush/Listen state transition for the current chunk."""
    confidence = float(intents.get("confidence") or 0.0)
    themes = list(intents.get("themes") or [])
    selected = list(intents.get("selected_context") or [])
    deranked = list(intents.get("deranked_context") or [])
    artifact_probe = dict(intents.get("artifact_probe") or {})
    trigger, reason = _hush_trigger(profile, chunk, entities, themes, selected, confidence, artifact_probe)
    state = "hush" if trigger else "listening"
    if trigger == "missing_entity_reference":
        state = "probe"
    profile["listen_state"] = state
    pulse = {
        "schema": PULSE_SCHEMA,
        "ts": _utc_now(),
        "chunk_id": chunk.get("chunk_id"),
        "chunk_index": int(chunk.get("index") or 0),
        "listen_state": state,
        "trigger": trigger or "steady_listen",
        "withheld_context": deranked[:6],
        "selected_context": selected[:6],
        "deranked_context": deranked[:6],
        "entities": [item["canonical"] for item in entities[:8]],
        "themes": themes,
        "confidence": round(confidence, 4),
        "artifact_probe": {
            "candidate_intent_keys": artifact_probe.get("candidate_intent_keys", []),
            "resolved_intent_keys": artifact_probe.get("resolved_intent_keys", []),
            "artifact_bindings": artifact_probe.get("artifact_bindings", []),
            "drift_events": (profile.get("artifact_probe_state") or {}).get("drift_events", [])[-6:],
            "mfs": artifact_probe.get("mfs", {}),
            "top_key": artifact_probe.get("top_key", ""),
            "top_confidence": artifact_probe.get("top_confidence", 0.0),
            "max_drift_score": artifact_probe.get("max_drift_score", 0.0),
            "has_probe": artifact_probe.get("has_probe", False),
            "has_mfs": artifact_probe.get("has_mfs", False),
        },
        "reason": reason,
    }
    profile.setdefault("hush_pulses", []).append(pulse)
    return pulse


def render_field_report(profile: dict[str, Any]) -> str:
    """Render a compact human-readable run report."""
    metrics = profile.get("metrics") or {}
    entities = sorted(
        (profile.get("entities") or {}).values(),
        key=lambda item: (item.get("support_count", 0), item.get("confidence", 0)),
        reverse=True,
    )
    nodes = sorted(
        (profile.get("intent_nodes") or {}).values(),
        key=lambda item: (item.get("support_count", 0), item.get("confidence", 0)),
        reverse=True,
    )
    lines = [
        "# IRT Field Profile Report",
        "",
        f"- run_id: `{profile.get('run_id', '')}`",
        f"- source_label: `{profile.get('source_label', '')}`",
        f"- mode: `{profile.get('mode', '')}`",
        f"- listen_state: `{profile.get('listen_state', '')}`",
        f"- chunks_processed: `{metrics.get('chunks_processed', 0)}`",
        f"- graph_stability: `{metrics.get('graph_stability', 0)}`",
        f"- entity_stability: `{metrics.get('entity_stability', 0)}`",
        f"- context_churn: `{metrics.get('context_churn', 0)}`",
        f"- unknown_rate: `{metrics.get('unknown_rate', 0)}`",
        f"- probe_rate: `{metrics.get('probe_rate', 0)}`",
        "",
        "## Entities",
        "",
    ]
    for entity in entities[:12]:
        lines.append(
            f"- `{entity.get('canonical')}` {entity.get('type')} "
            f"confidence `{entity.get('confidence')}` support `{entity.get('support_count')}`"
        )
    lines.extend(["", "## Intent Nodes", ""])
    for node in nodes[:12]:
        lines.append(
            f"- `{node.get('theme')}` confidence `{node.get('confidence')}` "
            f"support `{node.get('support_count')}` entities `{', '.join(node.get('entities') or [])}`"
        )
    lines.extend(["", "## Recent Hush Pulses", ""])
    for pulse in (profile.get("hush_pulses") or [])[-8:]:
        lines.append(
            f"- `{pulse.get('chunk_id')}` {pulse.get('listen_state')} "
            f"`{pulse.get('trigger')}`: {pulse.get('reason')}"
        )
    latest = (profile.get("artifact_probe_state") or {}).get("latest_resolution") or {}
    if latest:
        mfs = latest.get("mfs") if isinstance(latest.get("mfs"), dict) else {}
        lines.extend([
            "",
            "## Artifact Probe Resolution",
            "",
            f"- candidate_keys: `{len(latest.get('candidate_intent_keys') or [])}`",
            f"- resolved_keys: `{len(latest.get('resolved_intent_keys') or [])}`",
            f"- artifact_bindings: `{len(latest.get('artifact_bindings') or [])}`",
            f"- mfs_needed: `{mfs.get('mfs_needed', False)}`",
            f"- mfs_delta: `{mfs.get('model_favorability_score_delta', 0)}`",
        ])
    return "\n".join(lines) + "\n"


def _new_artifact_probe_state(source_meta: dict[str, Any]) -> dict[str, Any]:
    monthly = source_meta.get("monthly_intent_prior") if isinstance(source_meta, dict) else None
    return {
        "schema": "artifact_probe_intent_resolution/v1",
        "monthly_intent_prior": dict(monthly) if isinstance(monthly, dict) else {},
        "active_intent_keys": {},
        "candidate_intent_keys": [],
        "resolved_intent_keys": [],
        "artifact_bindings": [],
        "drift_events": [],
        "mfs_requests": [],
        "probe_requests": [],
        "latest_resolution": {},
        "updated_at": _utc_now(),
    }


def _extract_candidate_intent_keys(artifact: dict[str, Any]) -> list[dict[str, Any]]:
    text = str(artifact.get("text") or "")
    toks = set(_tokens(text))
    entity = next((item for item in artifact.get("entities") or [] if item), "unknown_entity")
    candidates = []
    for key, spec in INTENT_KEY_PATTERNS.items():
        terms = set(spec.get("terms") or set())
        hits = sorted(toks & terms)
        if not hits:
            continue
        confidence = min(0.96, 0.34 + len(hits) * 0.12 + (0.08 if entity != "unknown_entity" else 0.0))
        candidates.append({
            "key": key,
            "implied_trajectory": spec.get("trajectory", key),
            "evidence": hits[:12],
            "confidence": round(confidence, 4),
            "entity": entity,
            "source_artifact_id": artifact.get("artifact_id", ""),
            "temporal_context": {
                "chunk_index": artifact.get("chunk_index", 0),
                "timestamp": artifact.get("timestamp", ""),
            },
        })
    if not candidates:
        candidates.append({
            "key": "unknown_intent",
            "implied_trajectory": "artifact evidence did not expose a stable implied trajectory",
            "evidence": _tokens(text)[:8],
            "confidence": 0.22,
            "entity": entity,
            "source_artifact_id": artifact.get("artifact_id", ""),
            "temporal_context": {
                "chunk_index": artifact.get("chunk_index", 0),
                "timestamp": artifact.get("timestamp", ""),
            },
        })
    candidates.sort(key=lambda item: (float(item.get("confidence") or 0.0), item.get("key", "")), reverse=True)
    return candidates[:6]


def _adjacent_key_fit(key: str, active: dict[str, Any]) -> float:
    related = {
        "legacy_continuity": {"leadership_legitimacy", "base_consolidation"},
        "leadership_legitimacy": {"legacy_continuity", "base_consolidation"},
        "ai_modeling": {"vehicle_autonomy"},
        "vehicle_autonomy": {"ai_modeling"},
        "risk_governance": {"criticism_deflection"},
    }.get(key, set())
    if not related:
        return 0.0
    return max([float((active.get(rel) or {}).get("confidence") or 0.0) * 0.62 for rel in related] or [0.0])


def _key_contradiction_delta(key: str, active: dict[str, Any]) -> float:
    conflicts = INTENT_KEY_CONFLICTS.get(key, set())
    if not conflicts:
        return 0.0
    return max([float((active.get(conflict) or {}).get("confidence") or 0.0) for conflict in conflicts] or [0.0])


def _resolution_state(prior_fit: float, evidence: float, drift_score: float, contradiction: float) -> str:
    if evidence < 0.34:
        return "probe"
    if contradiction >= 0.55:
        return "contradict"
    if drift_score >= 0.72 and evidence >= 0.62:
        return "mfs"
    if drift_score >= 0.5:
        return "mutate"
    if prior_fit >= 0.58:
        return "reinforce"
    if prior_fit >= 0.22:
        return "extend"
    return "extend" if evidence >= 0.52 else "probe"


def _apply_active_key_update(
    state: dict[str, Any],
    resolved: dict[str, Any],
    candidate: dict[str, Any],
    binding: dict[str, Any],
) -> None:
    active = state.setdefault("active_intent_keys", {})
    key = str(resolved.get("key") or "")
    prior = active.get(key, {})
    support_count = int(prior.get("support_count") or 0) + 1
    confidence = max(
        float(prior.get("confidence") or 0.0) * 0.72,
        float(resolved.get("posterior_fit") or 0.0),
    )
    active[key] = {
        "key": key,
        "implied_trajectory": candidate.get("implied_trajectory", prior.get("implied_trajectory", "")),
        "confidence": round(min(0.99, confidence + min(0.18, support_count * 0.025)), 4),
        "support_count": support_count,
        "last_resolution": resolved.get("resolution", ""),
        "last_artifact_id": binding.get("artifact_id", ""),
        "last_seen": binding.get("timestamp", ""),
        "evidence": _last_items([*(prior.get("evidence") or []), *(candidate.get("evidence") or [])], 12),
    }


def _new_bayesian_state(source_meta: dict[str, Any]) -> dict[str, Any]:
    explicit_prior = source_meta.get("intent_prior") if isinstance(source_meta, dict) else None
    prior = _normalize_distribution(explicit_prior if isinstance(explicit_prior, dict) else _uniform_intent_prior())
    return {
        "schema": "bayesian_entity_intent_state/v1",
        "prior": prior,
        "posterior": {},
        "latest_update": {},
        "artifact_memory": [],
        "coupling_edges": [],
        "source_reliability": _coerce_probability(
            source_meta.get("source_reliability", 0.82) if isinstance(source_meta, dict) else 0.82,
            default=0.82,
        ),
        "updated_at": _utc_now(),
    }


def _current_intent_prior(profile: dict[str, Any]) -> dict[str, float]:
    state = profile.setdefault("bayesian_intent_state", _new_bayesian_state(profile.get("source_meta") or {}))
    posterior = state.get("posterior")
    base = posterior if isinstance(posterior, dict) and posterior else state.get("prior")
    prior = _normalize_distribution(base if isinstance(base, dict) else _uniform_intent_prior())
    uniform = _uniform_intent_prior()
    return _blend_distributions(prior, uniform, 0.12)


def _uniform_intent_prior() -> dict[str, float]:
    intents = [*THEME_WORDS.keys(), "unknown"]
    value = 1.0 / len(intents)
    return {intent: value for intent in intents}


def _evidence_likelihood(text: str, themes: list[str], semantic: dict[str, Any]) -> dict[str, float]:
    toks = set(_tokens(text))
    scores = {intent: 0.04 for intent in [*THEME_WORDS.keys(), "unknown"]}
    for theme, words in THEME_WORDS.items():
        hits = len(toks & words)
        if hits:
            scores[theme] += 0.28 + min(0.58, hits * 0.12)
    for theme in themes:
        if theme in scores:
            scores[theme] += 0.2
    if "live_field_intent_modeling" in (semantic.get("semantic_intents") or []):
        scores["field_sensing"] += 0.28
    if themes == ["unknown"]:
        scores["unknown"] += 0.55
    else:
        scores["unknown"] *= 0.4
    return _normalize_distribution(scores)


def _coupled_prior(
    profile: dict[str, Any],
    chunk: dict[str, Any],
    entities: list[dict[str, Any]],
    themes: list[str],
    prior: dict[str, float],
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    state = profile.setdefault("bayesian_intent_state", _new_bayesian_state(profile.get("source_meta") or {}))
    memory = list(state.get("artifact_memory") or [])[-10:]
    current = {
        "chunk_index": int(chunk.get("index") or 0),
        "tokens": _tokens(chunk.get("text") or ""),
        "themes": themes,
        "entities": [item["canonical"] for item in entities],
    }
    coupled = {key: float(value) * 0.35 for key, value in prior.items()}
    edges: list[dict[str, Any]] = []
    for artifact in memory:
        weight = _artifact_edge_weight(current, artifact)
        if weight <= 0.03:
            continue
        posterior = artifact.get("posterior") if isinstance(artifact.get("posterior"), dict) else {}
        for intent, probability in posterior.items():
            coupled[str(intent)] = coupled.get(str(intent), 0.0) + weight * float(probability)
        edges.append({
            "from_artifact": artifact.get("artifact_id", ""),
            "to_chunk": chunk.get("chunk_id", ""),
            "weight": round(weight, 4),
            "from_top": artifact.get("posterior_top", ""),
            "from_confidence": artifact.get("posterior_confidence", 0.0),
            "semantic_similarity": round(_jaccard(current["tokens"], artifact.get("tokens") or []), 4),
            "entity_overlap": round(_entity_overlap(current["entities"], artifact.get("entities") or []), 4),
            "time_decay": round(_time_decay(current["chunk_index"] - int(artifact.get("chunk_index") or 0)), 4),
        })
    edges.sort(key=lambda item: item["weight"], reverse=True)
    return _normalize_distribution(coupled), edges[:8]


def _artifact_edge_weight(current: dict[str, Any], artifact: dict[str, Any]) -> float:
    semantic_similarity = _jaccard(current.get("tokens") or [], artifact.get("tokens") or [])
    theme_overlap = _jaccard(current.get("themes") or [], artifact.get("themes") or [])
    entity_overlap = _entity_overlap(current.get("entities") or [], artifact.get("entities") or [])
    decay = _time_decay(int(current.get("chunk_index") or 0) - int(artifact.get("chunk_index") or 0))
    source_reliability = _coerce_probability(artifact.get("source_reliability", 0.82), default=0.82)
    raw = (
        0.34 * semantic_similarity
        + 0.26 * theme_overlap
        + 0.3 * entity_overlap
        + 0.1 * (1.0 if entity_overlap > 0 else 0.0)
    )
    return max(0.0, min(1.0, raw * decay * source_reliability))


def _time_decay(delta_chunks: int, half_life_chunks: float = 6.0) -> float:
    delta = max(0, int(delta_chunks or 0))
    if delta == 0:
        return 1.0
    return pow(0.5, delta / max(1.0, half_life_chunks))


def _bayes_update(prior: dict[str, float], likelihood: dict[str, float]) -> dict[str, float]:
    keys = set(prior) | set(likelihood)
    raw = {key: max(float(prior.get(key, 0.0)), 1e-9) * max(float(likelihood.get(key, 0.0)), 1e-9) for key in keys}
    return _normalize_distribution(raw)


def _blend_distributions(left: dict[str, float], right: dict[str, float], right_weight: float) -> dict[str, float]:
    weight = max(0.0, min(1.0, float(right_weight or 0.0)))
    keys = set(left) | set(right)
    blended = {
        key: float(left.get(key, 0.0)) * (1.0 - weight) + float(right.get(key, 0.0)) * weight
        for key in keys
    }
    return _normalize_distribution(blended)


def _normalize_distribution(values: dict[str, Any]) -> dict[str, float]:
    raw = {str(key): max(0.0, float(value)) for key, value in (values or {}).items()}
    total = sum(raw.values())
    if total <= 0:
        raw = _uniform_intent_prior()
        total = sum(raw.values())
    return {key: round(value / total, 6) for key, value in sorted(raw.items())}


def _top_probability(distribution: dict[str, float]) -> tuple[str, float]:
    if not distribution:
        return "unknown", 0.0
    key, value = max(distribution.items(), key=lambda item: item[1])
    return key, float(value)


def _normalized_entropy(distribution: dict[str, float]) -> float:
    import math

    probs = [float(value) for value in distribution.values() if float(value) > 0]
    if len(probs) <= 1:
        return 0.0
    entropy = -sum(p * math.log(p, 2) for p in probs)
    return entropy / math.log(len(probs), 2)


def _contradiction_pressure(
    coupling_edges: list[dict[str, Any]],
    likelihood: dict[str, float],
    posterior: dict[str, float],
) -> float:
    evidence_top, evidence_conf = _top_probability(likelihood)
    posterior_top, posterior_conf = _top_probability(posterior)
    pressure = 0.0
    for edge in coupling_edges:
        from_top = str(edge.get("from_top") or "")
        if not from_top or from_top == evidence_top:
            continue
        edge_weight = float(edge.get("weight") or 0.0)
        prior_conf = float(edge.get("from_confidence") or 0.0)
        evidence_rejects_prior = 1.0 - float(likelihood.get(from_top, 0.0))
        pressure = max(pressure, edge_weight * prior_conf * evidence_conf * evidence_rejects_prior)
    if posterior_top != evidence_top and evidence_conf > 0.45 and posterior_conf > 0.45:
        pressure = max(pressure, 0.45 * evidence_conf * posterior_conf)
    return min(1.0, pressure)


def _confidence_inflation(standalone: dict[str, float], posterior: dict[str, float]) -> float:
    posterior_top, posterior_conf = _top_probability(posterior)
    standalone_conf = float(standalone.get(posterior_top, 0.0))
    return max(0.0, posterior_conf - standalone_conf)


def _update_intent_nodes(
    profile: dict[str, Any],
    chunk: dict[str, Any],
    entities: list[dict[str, Any]],
    themes: list[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], float]:
    index = int(chunk.get("index") or 0)
    text = str(chunk.get("text") or "")
    if not themes:
        themes = ["unknown"]
    nodes = profile.setdefault("intent_nodes", {})
    entity_names = [item["canonical"] for item in entities]
    selected: list[dict[str, Any]] = []
    for theme in themes:
        key = theme
        node = nodes.get(key)
        if not node:
            node = {
                "node_id": "irt-node-" + _hash(key)[:16],
                "theme": theme,
                "entities": [],
                "confidence": 0.0,
                "support_count": 0,
                "drift_score": 0.0,
                "context_score": 0.0,
                "first_seen": index,
                "last_seen": index,
                "evidence_snippets": [],
                "score_parts": {},
            }
            nodes[key] = node
        previous_entities = set(node.get("entities") or [])
        entity_overlap = len(previous_entities & set(entity_names))
        for name in entity_names:
            if name not in node["entities"]:
                node["entities"].append(name)
        node["support_count"] = int(node.get("support_count") or 0) + 1
        temporal_gap = max(0, index - int(node.get("last_seen") or index))
        temporal_continuity = 1.0 if temporal_gap <= 1 else max(0.0, 1.0 - temporal_gap * 0.12)
        theme_overlap = 1.0
        entity_recurrence = min(1.0, (entity_overlap + max(0, int(node["support_count"]) - 1)) / 4.0)
        maif_similarity = _maif_theme_similarity(profile, theme, entity_names)
        drift_penalty = _drift_penalty(text, temporal_gap, entity_names, previous_entities)
        stale_penalty = min(0.35, max(0, temporal_gap - 4) * 0.08)
        context_score = (
            0.34 * theme_overlap
            + 0.26 * entity_recurrence
            + 0.2 * temporal_continuity
            + 0.12 * maif_similarity
            - 0.18 * drift_penalty
            - stale_penalty
        )
        context_score = max(0.0, min(1.0, context_score))
        node["last_seen"] = index
        node["confidence"] = round(min(0.99, 0.25 + int(node["support_count"]) * 0.15 + context_score * 0.35), 4)
        node["drift_score"] = round(drift_penalty + stale_penalty, 4)
        node["context_score"] = round(context_score, 4)
        node["evidence_snippets"] = _last_items([*node.get("evidence_snippets", []), text[:180]], 5)
        node["score_parts"] = {
            "theme_overlap": round(theme_overlap, 4),
            "entity_recurrence": round(entity_recurrence, 4),
            "temporal_continuity": round(temporal_continuity, 4),
            "maif_baseline_similarity": round(maif_similarity, 4),
            "contradiction_drift_penalty": round(drift_penalty, 4),
            "stale_context_penalty": round(stale_penalty, 4),
        }
        selected.append({
            "node_id": node["node_id"],
            "theme": theme,
            "context_score": node["context_score"],
            "confidence": node["confidence"],
            "entities": node["entities"][:6],
        })
    selected.sort(key=lambda item: (item["context_score"], item["confidence"]), reverse=True)
    selected_ids = {item["node_id"] for item in selected[:4]}
    deranked = [
        {
            "node_id": node.get("node_id"),
            "theme": node.get("theme"),
            "context_score": node.get("context_score", 0),
            "reason": "stale_or_weak_context",
        }
        for node in nodes.values()
        if node.get("node_id") not in selected_ids and float(node.get("context_score") or 0) < 0.42
    ]
    confidence = selected[0]["confidence"] if selected else 0.0
    return selected[:4], deranked[:8], float(confidence)


def _maybe_emit_void_probe(
    profile: dict[str, Any],
    chunk: dict[str, Any],
    entities: list[dict[str, Any]],
    themes: list[str],
    confidence: float,
    artifact_probe: dict[str, Any] | None = None,
) -> None:
    text = str(chunk.get("text") or "")
    toks = set(_tokens(text))
    ambiguous = bool(toks & PRONOUNS) and not entities
    artifact_probe = artifact_probe or {}
    max_drift = float(artifact_probe.get("max_drift_score") or 0.0)
    has_probe = bool(artifact_probe.get("has_probe"))
    has_mfs = bool(artifact_probe.get("has_mfs"))
    if confidence >= 0.42 and not ambiguous and themes != ["unknown"] and max_drift < 0.5 and not has_probe and not has_mfs:
        return
    target = themes[0] if themes else "unknown_intent"
    if ambiguous:
        reason = "missing_entity_reference"
    elif has_mfs:
        reason = "model_favorability_score"
        target = str(artifact_probe.get("top_key") or target)
    elif has_probe:
        reason = "intent_key_resolution"
        target = str(artifact_probe.get("top_key") or target)
    elif max_drift >= 0.5:
        reason = "profile_drift"
        target = str(artifact_probe.get("top_key") or target)
    else:
        reason = "low_confidence_or_unknown_theme"
    probe = {
        "question": _probe_question(reason, target),
        "target_entity_or_intent": target,
        "reason": reason,
        "confidence_before": round(confidence, 4),
        "confidence_after": round(max(confidence, 0.42), 4),
        "chunk_id": chunk.get("chunk_id"),
        "chunk_index": int(chunk.get("index") or 0),
    }
    profile.setdefault("void_probes", []).append(probe)


def _update_chunk_window(
    profile: dict[str, Any],
    chunk: dict[str, Any],
    themes: list[str],
    entities: list[dict[str, Any]],
    selected: list[dict[str, Any]],
    artifact_probe: dict[str, Any] | None = None,
) -> None:
    prior = profile.get("chunk_window") or {}
    summary_bits = list(prior.get("rolling_summary_bits") or [])
    entity_names = [item["canonical"] for item in entities[:4]]
    summary_bits.append(
        f"{chunk.get('chunk_id')}: {', '.join(themes[:2]) or 'unknown'}"
        f" / {', '.join(entity_names) or 'no entity'}"
    )
    profile["chunk_window"] = {
        "chunk_id": chunk.get("chunk_id"),
        "index": int(chunk.get("index") or 0),
        "start_ts": chunk.get("start_ts"),
        "end_ts": chunk.get("end_ts"),
        "text": str(chunk.get("text") or "")[:500],
        "themes": themes,
        "entities": entity_names,
        "selected_context": selected,
        "candidate_intent_keys": (artifact_probe or {}).get("candidate_intent_keys", []),
        "resolved_intent_keys": (artifact_probe or {}).get("resolved_intent_keys", []),
        "top_key": (artifact_probe or {}).get("top_key", ""),
        "rolling_summary": " | ".join(summary_bits[-8:]),
        "rolling_summary_bits": summary_bits[-8:],
    }


def _update_metrics(
    profile: dict[str, Any],
    semantic: dict[str, Any],
    themes: list[str],
    selected: list[dict[str, Any]],
    artifact_probe: dict[str, Any] | None = None,
) -> None:
    metrics = profile.setdefault("metrics", {})
    runtime = profile.setdefault("_runtime", {})
    processed = int(metrics.get("chunks_processed") or 0) + 1
    metrics["chunks_processed"] = processed
    if semantic.get("semantic_intent") == "unknown" and themes == ["unknown"]:
        runtime["unknown_chunks"] = int(runtime.get("unknown_chunks") or 0) + 1
    artifact_probe = artifact_probe or {}
    if float(artifact_probe.get("max_drift_score") or 0.0) >= 0.5:
        runtime["drift_chunks"] = int(runtime.get("drift_chunks") or 0) + 1
    selected_keys = [str(item.get("node_id")) for item in selected]
    previous = list(runtime.get("previous_selected_context") or [])
    metrics["context_churn"] = round(_churn(previous, selected_keys), 4)
    runtime["previous_selected_context"] = selected_keys
    nodes = list((profile.get("intent_nodes") or {}).values())
    entities = list((profile.get("entities") or {}).values())
    metrics["graph_stability"] = round(_support_stability(nodes), 4)
    metrics["entity_stability"] = round(_support_stability(entities), 4)
    metrics["unknown_rate"] = round(int(runtime.get("unknown_chunks") or 0) / max(1, processed), 4)
    metrics["probe_rate"] = round(len(profile.get("void_probes") or []) / max(1, processed), 4)
    metrics["resolution_entropy"] = round(_resolution_entropy(artifact_probe.get("resolved_intent_keys", [])), 4)
    metrics["drift_rate"] = round(int(runtime.get("drift_chunks") or 0) / max(1, processed), 4)
    metrics["mfs_trigger_rate"] = round(len((profile.get("artifact_probe_state") or {}).get("mfs_requests", [])) / max(1, processed), 4)


def _classify_themes(text: str, semantic: dict[str, Any]) -> list[str]:
    toks = set(_tokens(text))
    scored = []
    for theme, words in THEME_WORDS.items():
        hits = len(toks & words)
        if hits:
            scored.append((theme, hits))
    if "live_field_intent_modeling" in (semantic.get("semantic_intents") or []):
        scored.append(("field_sensing", 2))
    if not scored:
        return ["unknown"]
    scored.sort(key=lambda pair: (-pair[1], pair[0]))
    return [theme for theme, _hits in scored[:3]]


def _extract_entities(text: str) -> list[str]:
    found: list[str] = []
    for known in ENTITY_HINTS:
        if re.search(rf"\b{re.escape(known)}\b", text, re.I):
            found.append(known)
    for match in re.finditer(r"\b[A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*){0,3}\b", text):
        raw = match.group(0).strip()
        if raw in ENTITY_STOP or raw.lower() in {"ai", "irt"}:
            continue
        if len(raw) < 2:
            continue
        found.append(raw)
    out: list[str] = []
    seen: set[str] = set()
    for item in found:
        key = _entity_key(item)
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out[:12]


def _resolve_entity(entities: dict[str, Any], raw: str) -> str:
    raw = raw.strip()
    raw_key = _entity_key(raw)
    for existing in entities.values():
        canonical = str(existing.get("canonical") or "")
        aliases = [str(alias) for alias in existing.get("aliases") or []]
        names = [canonical, *aliases]
        if raw_key in {_entity_key(name) for name in names}:
            return canonical
        if " " not in raw:
            for name in names:
                parts = name.split()
                if parts and raw.lower() == parts[-1].lower():
                    return canonical
    if raw.lower() == "musk":
        return "Elon Musk"
    return raw


def _entity_type(name: str) -> str:
    if name in ENTITY_HINTS:
        return ENTITY_HINTS[name]
    if len(name.split()) >= 2:
        return "person"
    if name.isupper() or name in {"Tesla", "SpaceX", "OpenAI", "Twitter"}:
        return "organization"
    return "topic"


def _hush_trigger(
    profile: dict[str, Any],
    chunk: dict[str, Any],
    entities: list[dict[str, Any]],
    themes: list[str],
    selected: list[dict[str, Any]],
    confidence: float,
    artifact_probe: dict[str, Any] | None = None,
) -> tuple[str, str]:
    text = str(chunk.get("text") or "")
    toks = set(_tokens(text))
    previous = profile.get("chunk_window") or {}
    previous_themes = set(previous.get("themes") or [])
    current_themes = set(themes)
    topic_shift = bool(previous_themes and current_themes and not (previous_themes & current_themes))
    missing_reference = bool(toks & PRONOUNS) and not entities
    artifact_probe = artifact_probe or {}
    max_drift = float(artifact_probe.get("max_drift_score") or 0.0)
    has_mfs = bool(artifact_probe.get("has_mfs"))
    has_probe = bool(artifact_probe.get("has_probe"))
    source_reliability = _source_reliability(profile)
    if missing_reference:
        return "missing_entity_reference", "Pronouns or references appeared before a stable entity profile woke."
    if has_mfs:
        return "model_favorability_score", "High-drift intent resolution requires Model Favorability Score recalculation."
    if has_probe:
        return "intent_key_probe", "Candidate intent keys could not be resolved confidently against the profile."
    if max_drift >= 0.5:
        return "profile_drift", "Artifact-implied intent keys diverged from the active profile model."
    if source_reliability < 0.45:
        return "low_source_reliability", "Source reliability is too low to commit the posterior without review."
    if confidence < 0.32:
        return "low_confidence", "Chunk confidence fell below the Hush threshold; weak context is withheld."
    if "unknown" in themes:
        return "unknown_theme", "No stable theme matched this chunk."
    if topic_shift and (toks & DRIFT_WORDS or len(selected) <= 1):
        return "topic_shift", "Theme changed sharply from the prior chunk, so stale context is deranked."
    if len(selected) > 2:
        scores = [float(item.get("context_score") or 0.0) for item in selected]
        if scores and max(scores) - min(scores) < 0.08:
            return "context_churn", "Multiple context nodes competed with similar scores."
    return "", "Listening remained stable."


def _load_maif_baselines(root: Path) -> list[dict[str, Any]]:
    logs = Path(root) / "logs"
    baselines: list[dict[str, Any]] = []
    for path in sorted(logs.glob("repo_fingerprint_maif*.json"))[:8]:
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        for item in list(data.get("files") or [])[:80]:
            identity = str(item.get("identity") or "")
            if identity:
                baselines.append({
                    "identity": identity,
                    "tokens": set(_tokens(identity.replace("_", " "))),
                    "path_hash": item.get("path_hash", ""),
                })
    return baselines


def _maif_matches(profile: dict[str, Any], entity: str) -> list[dict[str, Any]]:
    etoks = set(_tokens(entity))
    matches = []
    for item in (profile.get("_runtime") or {}).get("maif_baselines") or []:
        overlap = etoks & set(item.get("tokens") or [])
        if overlap:
            matches.append({
                "identity": item.get("identity"),
                "score": round(len(overlap) / max(1, len(etoks)), 4),
                "path_hash": item.get("path_hash", ""),
            })
    matches.sort(key=lambda row: row["score"], reverse=True)
    return matches[:5]


def _maif_theme_similarity(profile: dict[str, Any], theme: str, entities: list[str]) -> float:
    toks = set(_tokens(" ".join([theme, *entities]).replace("_", " ")))
    if not toks:
        return 0.0
    best = 0.0
    for item in (profile.get("_runtime") or {}).get("maif_baselines") or []:
        overlap = toks & set(item.get("tokens") or [])
        best = max(best, len(overlap) / max(1, len(toks)))
    return min(1.0, best)


def _drift_penalty(text: str, temporal_gap: int, entity_names: list[str], previous_entities: set[str]) -> float:
    toks = set(_tokens(text))
    penalty = 0.0
    if toks & DRIFT_WORDS:
        penalty += 0.25
    if previous_entities and entity_names and not (previous_entities & set(entity_names)):
        penalty += 0.2
    if temporal_gap > 5:
        penalty += 0.15
    return min(1.0, penalty)


def _probe_question(reason: str, target: str) -> str:
    if reason == "missing_entity_reference":
        return "Which entity does this reference attach to?"
    if reason == "intent_key_resolution":
        return f"What evidence would resolve the implied `{target}` trajectory against the profile?"
    if reason == "model_favorability_score":
        return f"Should `{target}` change the entity's Model Favorability Score, or is this isolated drift?"
    if reason == "profile_drift":
        return f"Is `{target}` a real profile mutation or a one-artifact drift event?"
    if reason == "bayesian_contradiction":
        return f"Does this new evidence contradict the coupled `{target}` profile state, or is it a mode switch?"
    if reason == "posterior_entropy":
        return f"Which intent should win among the competing posterior states around `{target}`?"
    return f"What missing context would disambiguate `{target}`?"


def _support_stability(items: list[dict[str, Any]]) -> float:
    if not items:
        return 0.0
    return sum(min(int(item.get("support_count") or 0), 4) / 4 for item in items) / len(items)


def _resolution_entropy(resolutions: list[dict[str, Any]]) -> float:
    if not resolutions:
        return 0.0
    counts: dict[str, int] = {}
    for item in resolutions:
        state = str(item.get("resolution") or "unknown")
        counts[state] = counts.get(state, 0) + 1
    return _normalized_entropy({key: float(value) for key, value in counts.items()})


def _churn(previous: list[str], current: list[str]) -> float:
    if not previous and not current:
        return 0.0
    if not previous or not current:
        return 1.0
    prev = set(previous)
    curr = set(current)
    return 1.0 - (len(prev & curr) / max(1, len(prev | curr)))


def _source_reliability(profile: dict[str, Any]) -> float:
    state = profile.get("bayesian_intent_state") if isinstance(profile.get("bayesian_intent_state"), dict) else {}
    source_meta = profile.get("source_meta") if isinstance(profile.get("source_meta"), dict) else {}
    if "source_reliability" in state:
        return _coerce_probability(state.get("source_reliability"), default=0.82)
    return _coerce_probability(source_meta.get("source_reliability", 0.82), default=0.82)


def _coerce_probability(value: Any, default: float = 0.5) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(0.0, min(1.0, number))


def _jaccard(left: list[str] | set[str], right: list[str] | set[str]) -> float:
    lset = {str(item).lower() for item in left if str(item).strip()}
    rset = {str(item).lower() for item in right if str(item).strip()}
    if not lset and not rset:
        return 0.0
    return len(lset & rset) / max(1, len(lset | rset))


def _entity_overlap(left: list[str], right: list[str]) -> float:
    lset = {_entity_key(item) for item in left if str(item).strip()}
    rset = {_entity_key(item) for item in right if str(item).strip()}
    if not lset or not rset:
        return 0.0
    return len(lset & rset) / max(1, min(len(lset), len(rset)))


def _snippet(text: str, term: str, radius: int = 70) -> str:
    match = re.search(re.escape(term), text, re.I)
    if not match:
        return text[: radius * 2]
    start = max(0, match.start() - radius)
    end = min(len(text), match.end() + radius)
    return text[start:end].strip()


def _tokens(text: str) -> list[str]:
    return [token for token in re.findall(r"[a-zA-Z0-9]+", str(text).lower()) if len(token) >= 2]


def _entity_key(text: str) -> str:
    return "_".join(_tokens(text)) or "unknown"


def _hash(text: str) -> str:
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def _last_items(items: list[Any], limit: int) -> list[Any]:
    return [item for item in items if item][-limit:]


def _parse_ts(value: str) -> datetime:
    raw = str(value).replace("Z", "+00:00")
    parsed = datetime.fromisoformat(raw)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = [
    "analyze_transcription_against_profile",
    "apply_intent_resolutions",
    "build_irt_profile",
    "chunk_transcript",
    "emit_hush_pulse",
    "probe_artifact_for_intent_keys",
    "process_speech_chunk",
    "render_field_report",
    "resolve_intent_keys_against_profile",
    "select_entity_profiles",
    "should_run_mfs",
    "update_bayesian_intent_state",
]
