"""Hush intent runtime and repo-room classifier.

Hush is the intent reconstruction authority for the file-substrate loop. This
module stays deterministic: it reads local telemetry, repo fingerprints, file
sim state, and intent history, then emits a mutation fence plus wakeable file
packets for downstream orchestrators.
"""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.file_number_key_identity_seq001_v001 import file_identity_card

SCHEMA = "hush_intent_runtime/v1"
LATEST = "logs/hush_intent_runtime_latest.json"
HISTORY = "logs/hush_intent_runtime.jsonl"
MARKDOWN = "logs/hush_intent_runtime.md"

LOCAL_REPO = "keystroke_telemetry"
LOW_CONFIDENCE = 0.22
CROSS_REPO_MARGIN = 0.08

LOCAL_TERMS = {
    "keystroke", "telemetry", "file", "files", "sim", "orchestrator",
    "opus", "runtime", "prompt", "encoding", "intent", "context0",
    "rename", "inator", "deepseek", "copilot", "codex", "pigeon",
    "micro", "agents", "substrate", "mail", "email",
}
MAIF_TERMS = {
    "maif", "myaifingerprint", "linkrouter", "hush", "entity",
    "entities", "directory", "audit", "auditor", "consensus", "drift",
    "whisperer", "whisper", "irt", "field", "reputation",
}


def classify_active_repo(
    root: Path,
    prompt: str,
    deleted_words: list[str] | None = None,
    context_selection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify the active repo before any mutation-capable routing."""
    root = Path(root)
    tokens = set(_tokens(" ".join([prompt or "", *(deleted_words or [])])))
    candidates = [_local_candidate(tokens, context_selection or {})]
    candidates.extend(_fingerprint_candidates(root, tokens, context_selection or {}))
    candidates = sorted(candidates, key=lambda row: (-row["score"], row["repo"]))
    top = candidates[0] if candidates else _candidate("unknown", 0, [], "none")
    second = candidates[1] if len(candidates) > 1 else _candidate("none", 0, [], "none")
    confidence = round(float(top.get("score") or 0), 4)
    cross_repo = second["score"] >= LOW_CONFIDENCE and (confidence - second["score"]) <= CROSS_REPO_MARGIN
    low = confidence < LOW_CONFIDENCE
    active_repo = "ambiguous" if cross_repo or low else top["repo"]
    fence = "blocked" if active_repo == "ambiguous" else "open"
    if low:
        reason = "repo confidence below mutation threshold"
    elif cross_repo:
        reason = "multiple repo rooms are plausible; mutation requires an explicit repo lock"
    else:
        reason = f"{top['repo']} matched {', '.join(top.get('matched_terms') or ['repo signals'])}"
    return {
        "schema": "hush_repo_classification/v1",
        "ts": _now(),
        "active_repo": active_repo,
        "repo_confidence": confidence,
        "repo_candidates": candidates[:5],
        "mutation_fence": fence,
        "reason": reason,
    }


def build_hush_intent_runtime(root: Path, prompt: str = "", *, write: bool = True) -> dict[str, Any]:
    """Build the persistent Hush intent-map packet for orchestration."""
    root = Path(root)
    journal = _jsonl_tail(root / "logs" / "prompt_journal.jsonl", 8)
    latest_prompt = journal[-1] if journal else {}
    current_prompt = str(prompt or latest_prompt.get("msg") or "")
    deleted = list(latest_prompt.get("deleted_words") or [])
    context_pack = _json(root / "logs" / "dynamic_context_pack.json")
    context_selection = context_pack.get("context_selection") if isinstance(context_pack.get("context_selection"), dict) else {}
    repo = classify_active_repo(root, current_prompt, deleted, context_selection)
    semantic = _json(root / "logs" / "semantic_profile_latest.json")
    intent_graph = _json(root / "logs" / "intent_graph_latest.json")
    sim = _json(root / "logs" / "file_self_sim_learning_latest.json")
    outcome = _json(root / "logs" / "codex_edit_outcome_latest.json")
    intent_moves = _intent_moves(current_prompt, intent_graph)
    packets = _file_packets(root, repo, sim, current_prompt)
    result = {
        "schema": SCHEMA,
        "ts": _now(),
        "name": "Hush",
        "role": "persistent_intent_reconstruction_agent",
        "operator_prompt": current_prompt,
        "deleted_words": deleted,
        "repo_classification": repo,
        "intent_map": _intent_map(journal, semantic, intent_moves),
        "intent_moves": intent_moves,
        "file_packets": packets,
        "workflow": [
            "operator signal",
            "Hush intent map",
            "active repo",
            "intent moves",
            "wake order",
            "file packets",
            "sim/delegate jobs",
            "validation gate",
            "memory update",
        ],
        "runtime_authority": {
            "mutation_fence": repo["mutation_fence"],
            "allowed_when_blocked": ["read", "plan", "artifact_only", "ask_for_repo_lock"],
            "source_mutation_allowed": repo["mutation_fence"] == "open",
        },
        "repo_room_context": _repo_room_context(root, repo),
        "recent_outcome": _recent_outcome(outcome),
        "whisper_irt": {
            "status": "modeled_future_layer",
            "capability": "live field intent whispering is memory-hooked here, not deployed in v1",
        },
        "paths": {"latest": LATEST, "history": HISTORY, "markdown": MARKDOWN},
    }
    if write:
        _write_json(root / LATEST, result)
        _append_jsonl(root / HISTORY, result)
        (root / MARKDOWN).write_text(render_hush_intent_runtime(result), encoding="utf-8")
    return result


def render_hush_intent_runtime(runtime: dict[str, Any]) -> str:
    repo = runtime.get("repo_classification") or {}
    lines = [
        "# Hush Intent Runtime",
        "",
        f"- active repo: `{repo.get('active_repo')}`",
        f"- confidence: `{repo.get('repo_confidence')}`",
        f"- mutation fence: `{repo.get('mutation_fence')}`",
        f"- reason: {repo.get('reason')}",
        "",
        "## Intent Moves",
    ]
    for move in runtime.get("intent_moves") or []:
        lines.append(f"- `{move.get('intent_key')}` -> {move.get('summary')}")
    lines.extend(["", "## File Packets"])
    for packet in runtime.get("file_packets") or []:
        lines.append(
            f"- `{packet.get('file_identity')}` {packet.get('operator_display_name')}: "
            f"{packet.get('current_responsibility')} [{packet.get('wake_reason')}]"
        )
    lines.extend(["", "## Runtime Authority"])
    auth = runtime.get("runtime_authority") or {}
    lines.append(f"- source mutation allowed: `{auth.get('source_mutation_allowed')}`")
    lines.append(f"- blocked fallback: `{', '.join(auth.get('allowed_when_blocked') or [])}`")
    return "\n".join(lines) + "\n"


def _local_candidate(tokens: set[str], context: dict[str, Any]) -> dict[str, Any]:
    matched = sorted(tokens & LOCAL_TERMS)
    score = len(matched) / 8
    for item in context.get("files") or []:
        name = str(item.get("name") if isinstance(item, dict) else item).lower()
        if name.startswith(("src", "tc_", "file_", "opus_", "pigeon", "numeric")):
            score += 0.08
    return _candidate(LOCAL_REPO, min(score, 1.0), matched, "local telemetry repo")


def _fingerprint_candidates(root: Path, tokens: set[str], context: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for path in sorted((root / "logs").glob("repo_fingerprint_*.json")):
        data = _json(path)
        label = str(data.get("label") or path.stem.replace("repo_fingerprint_", ""))
        identity_terms = set()
        for item in data.get("files") or []:
            identity_terms.update(_tokens(str(item.get("identity") or "")))
        domain_terms = set(MAIF_TERMS if label in {"maif_auditor", "linkrouter", "linkrouter_ai"} else [])
        label_terms = set(_tokens(label.replace("_", " ")))
        matched = sorted(tokens & (identity_terms | domain_terms | label_terms))
        score = len(matched) / 7
        for item in context.get("files") or []:
            name = str(item.get("name") if isinstance(item, dict) else item).lower()
            if name.startswith(label):
                score += 0.12
        rows.append(_candidate(label, min(score, 1.0), matched, f"repo fingerprint {path.name}"))
    if not rows and tokens & MAIF_TERMS:
        matched = sorted(tokens & MAIF_TERMS)
        rows.append(_candidate("maif_auditor", min(len(matched) / 7, 1.0), matched, "MAIF domain map"))
    return rows


def _candidate(repo: str, score: float, matched: list[str], source: str) -> dict[str, Any]:
    return {"repo": repo, "score": round(float(score), 4), "matched_terms": matched[:12], "source": source}


def _intent_moves(prompt: str, graph: dict[str, Any]) -> list[dict[str, Any]]:
    lower = prompt.lower()
    specs = [
        ("hush_intent_runtime", {"hush", "runtime", "reconstruction", "persistent", "intent map"}),
        ("repo_classification", {"repo", "root", "context0", "linkrouter", "maif", "codebase"}),
        ("linkrouter_file_room_access", {"linkrouter", "maif", "files", "call files"}),
        ("file_mail_quality_gate", {"email", "emails", "mail", "text"}),
        ("file_identity_narrative", {"rename", "identity", "inator", "names", "responsible"}),
        ("field_whisper_irt_future_layer", {"whisper", "irt", "field", "intent"}),
    ]
    moves = []
    for name, hints in specs:
        if any(hint in lower for hint in hints):
            moves.append(_move(name, prompt))
    if not moves:
        for item in (graph.get("intents") or [])[:4]:
            moves.append({
                "name": str(item.get("target") or "intent_move"),
                "intent_key": str(item.get("intent_key") or "hush:route:intent_move:minor"),
                "summary": str(item.get("segment") or item.get("why") or "intent graph move"),
                "files": item.get("files") or [],
            })
    return moves[:8] or [_move("general_intent_reconstruction", prompt)]


def _move(name: str, prompt: str) -> dict[str, Any]:
    return {
        "name": name,
        "intent_key": f"hush:build:{name}:patch",
        "summary": _summary_for_move(name, prompt),
        "files": _files_for_move(name),
    }


def _summary_for_move(name: str, prompt: str) -> str:
    summaries = {
        "hush_intent_runtime": "make Hush own persistent intent reconstruction and extended runtime state",
        "repo_classification": "classify active repo before manifest scoring and block unsafe mutation",
        "linkrouter_file_room_access": "treat LinkRouter/MAIF fingerprints as callable repo-room context",
        "file_mail_quality_gate": "stop emails that do not carry learned/done/next/need signal",
        "file_identity_narrative": "make file packets expose identity, responsibility, and mutation state",
        "field_whisper_irt_future_layer": "reserve live field intent whisper hooks for non-coding IRT",
    }
    return summaries.get(name, _snip(prompt, 180))


def _files_for_move(name: str) -> list[str]:
    table = {
        "hush_intent_runtime": ["src/hush_intent_runtime_seq001_v001.py", "src/opus_orchestrator_runtime_seq001_v001.py"],
        "repo_classification": ["src/hush_intent_runtime_seq001_v001.py", "src/ai_fingerprint_repo_seq001_v001.py"],
        "linkrouter_file_room_access": ["src/ai_fingerprint_repo_seq001_v001.py", "docs/LINKROUTER_AI_MAP.md"],
        "file_mail_quality_gate": ["src/file_email_plugin_seq001_v001.py", "src/file_email_text_chain_seq001_v001.py"],
        "file_identity_narrative": ["src/file_number_key_identity_seq001_v001.py", "src/file_interlinked_naming_sim_seq001_v001.py"],
        "field_whisper_irt_future_layer": ["src/hush_intent_runtime_seq001_v001.py"],
    }
    return table.get(name, [])


def _file_packets(root: Path, repo: dict[str, Any], sim: dict[str, Any], prompt: str) -> list[dict[str, Any]]:
    if repo.get("active_repo") not in {LOCAL_REPO, "ambiguous"}:
        return _repo_fingerprint_packets(root, str(repo.get("active_repo")), repo)
    rows = []
    wake = sim.get("wake_order") if isinstance(sim.get("wake_order"), list) else []
    packets = sim.get("learning_packets") if isinstance(sim.get("learning_packets"), list) else []
    by_file = {str(p.get("file")): p for p in packets if isinstance(p, dict) and p.get("file")}
    for item in wake[:8]:
        file = str(item.get("file") or "")
        if not file:
            continue
        source_packet = by_file.get(file, {})
        rows.append(_local_file_packet(file, item, source_packet, repo))
    if not rows:
        for file in _files_for_move("hush_intent_runtime")[:3]:
            rows.append(_local_file_packet(file, {"wake_reason": "Hush runtime bootstrap"}, {}, repo))
    return rows


def _local_file_packet(file: str, wake: dict[str, Any], source_packet: dict[str, Any], repo: dict[str, Any]) -> dict[str, Any]:
    identity = file_identity_card(file, _file_kind(file), str(wake.get("wake_reason") or "current prompt wake"))
    fence = repo.get("mutation_fence")
    return {
        "schema": "hush_file_packet/v1",
        "repo": LOCAL_REPO,
        "file": file,
        "file_identity": identity["number_key"],
        "operator_display_name": identity["operator_display_name"],
        "current_responsibility": _responsibility(file, source_packet),
        "last_change_state": identity["mutation_name"],
        "wake_reason": str(wake.get("wake_reason") or "selected by Hush runtime"),
        "allowed_actions": _allowed_actions(fence),
        "blocked_actions": _blocked_actions(fence),
        "neighbor_context": _neighbors(wake, source_packet),
        "validation_gate": _validation_gate(wake, source_packet),
        "memory_write_target": f"logs/file_memory/{file.replace('/', '__')}.json",
    }


def _repo_fingerprint_packets(root: Path, label: str, repo: dict[str, Any]) -> list[dict[str, Any]]:
    data = _json(root / "logs" / f"repo_fingerprint_{label}.json")
    rows = []
    for item in (data.get("files") or [])[:8]:
        identity = str(item.get("identity") or "")
        rows.append({
            "schema": "hush_file_packet/v1",
            "repo": label,
            "file": identity,
            "file_identity": identity,
            "operator_display_name": "Repo-Room-" + identity.replace("_", "-")[:80],
            "current_responsibility": "closed-repo context participant; source remains privacy fenced",
            "last_change_state": "fingerprint_indexed_not_source_mutated",
            "wake_reason": "active repo fingerprint matched operator intent",
            "allowed_actions": _allowed_actions(repo.get("mutation_fence")),
            "blocked_actions": ["source_mutation", "raw_source_exfiltration"],
            "neighbor_context": [],
            "validation_gate": ["repo lock", "operator opens exact file before mutation"],
            "memory_write_target": f"logs/file_memory/{identity}.json",
        })
    return rows


def _allowed_actions(fence: str) -> list[str]:
    if fence == "open":
        return ["read", "plan", "artifact", "validated_patch_after_approval"]
    return ["read", "plan", "artifact_only", "ask_for_repo_lock"]


def _blocked_actions(fence: str) -> list[str]:
    blocked = ["autonomous_overwrite", "cross_repo_mutation"]
    if fence == "blocked":
        blocked.append("source_mutation")
    return blocked


def _responsibility(file: str, packet: dict[str, Any]) -> str:
    profile = packet.get("responsibility_profile") if isinstance(packet.get("responsibility_profile"), dict) else {}
    declared = str(profile.get("declared_role") or "")
    if declared:
        return declared
    stem = Path(file).stem
    words = _tokens(stem.replace("_", " "))
    return " ".join(words[:8]) or "file substrate participant"


def _neighbors(wake: dict[str, Any], packet: dict[str, Any]) -> list[str]:
    out = []
    out.extend(str(x) for x in wake.get("known_neighbors") or [] if x)
    for item in wake.get("context_veins") or []:
        if isinstance(item, dict) and item.get("file"):
            out.append(str(item["file"]))
    out.extend(str(x) for x in packet.get("known_neighbors") or [] if x)
    return list(dict.fromkeys(out))[:8]


def _validation_gate(wake: dict[str, Any], packet: dict[str, Any]) -> list[str]:
    tests = list(wake.get("tests") or packet.get("tests") or [])
    if tests:
        return [f"py -m pytest {tests[0]} -q"]
    file = str(wake.get("file") or packet.get("file") or "")
    return [f"py -m py_compile {file}"] if file.endswith(".py") else ["operator approval required"]


def _file_kind(file: str) -> str:
    name = Path(file).name
    if name.startswith("test_"):
        return "test"
    if any(ord(ch) > 127 for ch in name):
        return "symbolic_pigeon_name"
    if re.search(r"_seq\d+_v\d+", name):
        return "versioned_module"
    return "stable_facade"


def _intent_map(journal: list[dict[str, Any]], semantic: dict[str, Any], moves: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(row.get("intent") or "unknown") for row in journal)
    return {
        "schema": "hush_persistent_intent_map/v1",
        "recent_prompt_count": len(journal),
        "recent_intents": dict(counts),
        "semantic_intents": semantic.get("semantic_intents") or ([semantic.get("semantic_intent")] if semantic.get("semantic_intent") else []),
        "active_threads": [move["name"] for move in moves],
    }


def _repo_room_context(root: Path, repo: dict[str, Any]) -> dict[str, Any]:
    active = repo.get("active_repo")
    if active and active not in {LOCAL_REPO, "ambiguous"}:
        data = _json(root / "logs" / f"repo_fingerprint_{active}.json")
        return {
            "repo": active,
            "privacy": data.get("privacy", "closed"),
            "files_indexed": data.get("files_indexed", 0),
            "callable_context": [row.get("identity") for row in (data.get("files") or [])[:8]],
        }
    return {"repo": active, "privacy": "local", "callable_context": []}


def _recent_outcome(outcome: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": outcome.get("status") or outcome.get("decision") or "",
        "reason": _snip(outcome.get("reason") or outcome.get("summary") or "", 220),
    }


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z][A-Za-z0-9_]{1,}", str(text or ""))]


def _snip(text: Any, limit: int) -> str:
    one = " ".join(str(text or "").split())
    return one if len(one) <= limit else one[: max(0, limit - 3)].rstrip() + "..."


def _json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace")) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _jsonl_tail(path: Path, count: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines()[-count:]:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return rows


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, sort_keys=True) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

