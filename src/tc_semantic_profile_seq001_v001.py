"""Semantic profile and numeric encoding for prompt intent events.

This layer is deliberately local and deterministic. It records what the
operator appeared to do with a prompt, updates durable profile facts, and
returns a compact numeric signature that other prompt routers can match.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROFILE_SCHEMA = "semantic_profile/v1"
FACT_PATTERNS = [
    (re.compile(r"\bmy name is\s+([a-zA-Z][a-zA-Z .'-]{1,48})", re.I), "name"),
    (re.compile(r"\bcall me\s+([a-zA-Z][a-zA-Z .'-]{1,48})", re.I), "name"),
]
INTRO_WORDS = {"hi", "hello", "hey", "yo", "sup"}
SYSTEM_WORDS = {
    "semantic", "profile", "intent", "numeric", "neumeric", "encoding",
    "thought", "completer", "prompt", "matching", "every",
}
ORCHESTRATOR_WORDS = {
    "orchestrator", "orchestrate", "approval", "approve", "guard", "guarded",
    "consensus", "10q", "sim", "sims", "copilot", "deepseek", "autonomous",
    "rewrite", "fixes",
}
EMAIL_WORDS = {"email", "emails", "resend", "outbox", "alert", "alerts", "mail"}
MONITOR_WORDS = {"monitor", "monitoring", "watch", "observe", "observatory", "telemetry"}
OPERATOR_STATE_WORDS = {
    "operator", "operatorstate", "state", "profile", "fingerprint", "live",
    "model", "primary", "intent", "baseline",
}
FILE_VOICE_WORDS = {
    "old", "friend", "sycophantic", "tone", "voice", "comedy", "mail",
    "emails", "feel", "centered", "centeread", "actionable", "personalization",
    "personalized", "planning", "learned", "done", "gpt", "terrible",
}
REASONING_WORDS = {"reasoning", "reason", "why", "logic", "receipts", "because"}
FILE_MEMORY_WORDS = {
    "memory", "memories", "knowledge", "remember", "store", "stored",
    "messages", "thread", "threads", "mailbox", "manage", "files",
}
LIVE_FIELD_WORDS = {
    "microphone", "microphones", "whisper", "speech", "speeches", "podcast",
    "field", "entity", "entities", "hush", "pulse", "pulses", "irt",
    "void", "probe", "probes", "listen", "listening",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return fallback


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9_]+", text.lower())


def _clean_value(value: str) -> str:
    value = re.split(r"\s+\b(?:and|then|so|because|but|with|that)\b|\s*(?:-|>|,|\.|;|\n)\s*", value.strip(), maxsplit=1)[0]
    value = re.sub(r"\s+", " ", value)
    return value[:64]


def _numeric_signature(parts: list[str], width: int = 12) -> dict[str, Any]:
    seed = "|".join(p for p in parts if p)
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    raw = [int.from_bytes(digest[i:i + 2], "big") for i in range(0, width * 2, 2)]
    return {
        "algorithm": "sha256_u16_v1",
        "seed": seed[:180],
        "vector": raw,
        "unit": [round(x / 65535, 5) for x in raw],
        "hex": hashlib.sha256(seed.encode("utf-8")).hexdigest()[:24],
    }


def load_profile(root: Path) -> dict[str, Any]:
    profile = _read_json(Path(root) / "logs" / "semantic_profile.json", {})
    if not isinstance(profile, dict) or profile.get("schema") != PROFILE_SCHEMA:
        profile = {"schema": PROFILE_SCHEMA, "created_at": _utc_now(), "facts": {}, "intents": {}}
    profile.setdefault("facts", {})
    profile.setdefault("intents", {})
    return profile


def _find_profile_matches(text: str, profile: dict[str, Any]) -> list[dict[str, Any]]:
    lower = text.lower()
    matches: list[dict[str, Any]] = []
    for fact_type, fact in sorted((profile.get("facts") or {}).items()):
        value = str((fact or {}).get("value") or "").strip()
        if value and re.search(rf"\b{re.escape(value.lower())}\b", lower):
            matches.append({
                "fact_type": fact_type,
                "value": value,
                "confidence": float((fact or {}).get("confidence", 1.0)),
                "numeric_encoding": _numeric_signature([fact_type, value]),
            })
    return matches


def _extract_fact_updates(text: str) -> list[dict[str, Any]]:
    updates: list[dict[str, Any]] = []
    for pattern, fact_type in FACT_PATTERNS:
        for match in pattern.finditer(text):
            value = _clean_value(match.group(1))
            if value:
                updates.append({
                    "fact_type": fact_type,
                    "value": value[:1].upper() + value[1:],
                    "confidence": 1.0,
                    "source_phrase": match.group(0)[:120],
                })
    return updates


def classify_semantic_intents(text: str, profile: dict[str, Any]) -> dict[str, Any]:
    toks = set(_tokens(text))
    updates = _extract_fact_updates(text)
    matches = _find_profile_matches(text, profile)
    intents: list[str] = []
    if toks & INTRO_WORDS:
        intents.append("introduction")
    if updates:
        intents.append("share_information")
    if matches:
        intents.append("profile_reference")
    if len(toks & SYSTEM_WORDS) >= 3:
        intents.append("intent_system_design")
    if len(toks & ORCHESTRATOR_WORDS) >= 2:
        intents.append("code_orchestration")
    if toks & EMAIL_WORDS:
        intents.append("telemetry_email")
    if toks & MONITOR_WORDS:
        intents.append("monitoring")
    if "operatorstate" in toks or len(toks & OPERATOR_STATE_WORDS) >= 2:
        intents.append("operator_state_modeling")
    if len(toks & FILE_VOICE_WORDS) >= 2:
        intents.append("file_voice_design")
    if toks & REASONING_WORDS:
        intents.append("reasoning_depth")
    if (toks & EMAIL_WORDS) and len(toks & FILE_MEMORY_WORDS) >= 2:
        intents.append("file_memory_management")
    if len(toks & LIVE_FIELD_WORDS) >= 3 or {"void", "probe"} <= toks:
        intents.append("live_field_intent_modeling")
    if not intents:
        intents.append("unknown")
    if "share_information" in intents:
        primary = "share_information"
    elif "live_field_intent_modeling" in intents:
        primary = "live_field_intent_modeling"
    elif "code_orchestration" in intents:
        primary = "code_orchestration"
    elif "operator_state_modeling" in intents:
        primary = "operator_state_modeling"
    elif "file_memory_management" in intents:
        primary = "file_memory_management"
    elif "file_voice_design" in intents:
        primary = "file_voice_design"
    elif "telemetry_email" in intents:
        primary = "telemetry_email"
    elif "reasoning_depth" in intents:
        primary = "reasoning_depth"
    elif "monitoring" in intents:
        primary = "monitoring"
    else:
        primary = intents[0]
    return {
        "semantic_intent": primary,
        "semantic_intents": intents,
        "profile_updates": updates,
        "profile_matches": matches,
    }


def log_semantic_profile_event(
    root: Path,
    text: str,
    source: str = "thought_completer",
    intent_key: str | None = None,
    deleted_words: list[str] | None = None,
) -> dict[str, Any]:
    root = Path(root)
    text = str(text or "").strip()
    profile = load_profile(root)
    classified = classify_semantic_intents(text, profile)
    now = _utc_now()
    for update in classified["profile_updates"]:
        fact_type = update["fact_type"]
        prior = (profile.get("facts") or {}).get(fact_type, {})
        profile["facts"][fact_type] = {
            **prior,
            "value": update["value"],
            "confidence": update["confidence"],
            "updated_at": now,
            "last_source": source,
            "numeric_encoding": _numeric_signature([fact_type, update["value"]]),
        }
    for intent in classified["semantic_intents"]:
        profile["intents"][intent] = int(profile["intents"].get(intent, 0)) + 1
    profile["updated_at"] = now
    signature_parts = [
        classified["semantic_intent"],
        text,
        intent_key or "",
        " ".join(deleted_words or []),
        *[f"{m['fact_type']}={m['value']}" for m in classified["profile_matches"]],
        *[f"{u['fact_type']}={u['value']}" for u in classified["profile_updates"]],
    ]
    event = {
        "ts": now,
        "source": source,
        "text": text,
        "intent_key": intent_key or "",
        "deleted_words": deleted_words or [],
        **classified,
        "numeric_encoding": _numeric_signature(signature_parts),
        "completion_hint": _completion_hint(classified),
    }
    logs = root / "logs"
    _write_json(logs / "semantic_profile.json", profile)
    _write_json(logs / "semantic_profile_latest.json", event)
    _append_jsonl(logs / "semantic_profile_events.jsonl", event)
    return event


def _completion_hint(classified: dict[str, Any]) -> str:
    matches = classified.get("profile_matches") or []
    if matches:
        first = matches[0]
        return f"profile:{first['fact_type']}={first['value']}"
    updates = classified.get("profile_updates") or []
    if updates:
        first = updates[0]
        return f"remember:{first['fact_type']}={first['value']}"
    if "introduction" in (classified.get("semantic_intents") or []):
        return "intent:introduction"
    if "code_orchestration" in (classified.get("semantic_intents") or []):
        return "intent:code_orchestration"
    if "live_field_intent_modeling" in (classified.get("semantic_intents") or []):
        return "intent:live_field_intent_modeling"
    if "operator_state_modeling" in (classified.get("semantic_intents") or []):
        return "intent:operator_state_modeling"
    if "file_memory_management" in (classified.get("semantic_intents") or []):
        return "intent:file_memory_management"
    if "file_voice_design" in (classified.get("semantic_intents") or []):
        return "intent:file_voice_design"
    if "telemetry_email" in (classified.get("semantic_intents") or []):
        return "intent:telemetry_email"
    if "reasoning_depth" in (classified.get("semantic_intents") or []):
        return "intent:reasoning_depth"
    if "monitoring" in (classified.get("semantic_intents") or []):
        return "intent:monitoring"
    return ""
