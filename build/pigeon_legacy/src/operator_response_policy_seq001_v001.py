"""Operator response policy and reward loop.

This module makes the response surface explicit. Codex/Copilot/file mail all
read the same local policy, log the same response metadata, and update a small
weighted reward model from explicit and passive operator signals.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

POLICY_SCHEMA = "operator_response_policy/v1"
STYLE_MODEL_SCHEMA = "response_style_model/v1"
REWARD_EVENT_SCHEMA = "response_reward_event/v1"

POLICY_START = "<!-- codex:operator-response-policy -->"
POLICY_END = "<!-- /codex:operator-response-policy -->"

REWARD_WEIGHTS = {
    "thinking_momentum": 0.45,
    "intent_extraction_accuracy": 0.25,
    "code_mutation_readiness": 0.20,
    "comedy_style_resonance": 0.10,
}

REQUIRED_SECTIONS = [
    "Operator read",
    "Intent moves",
    "Probe files",
    "Next mutation",
    "File quote",
]

PRIORITY_ORDER = [
    "thinking_momentum",
    "intent_extraction",
    "autonomous_code_mutation_readiness",
    "comedy_file_personality",
]

RESPONSE_ARMS = {
    "probe_council": {
        "summary": "Default intent-first probe layer. Read the operator, wake files, propose the bounded next mutation.",
        "required_sections": REQUIRED_SECTIONS,
        "banned_behaviors": ["generic encouragement", "status-only mail", "unbounded rewrite claims"],
    },
    "surgical_engineer": {
        "summary": "Terse patch/test lane. Explain the exact change, verification, and remaining risk.",
        "required_sections": ["Operator read", "Next mutation", "Validation"],
        "banned_behaviors": ["performative comedy", "long ontology recap", "unverified confidence"],
    },
    "old_friend_file_mail": {
        "summary": "Conversational memory lane for file mail and durable file knowledge.",
        "required_sections": ["Operator read", "What I learned", "What I did", "Next I am planning", "I need"],
        "banned_behaviors": ["dashboard memo voice", "rigid 10Q wall in visible mail", "defensive file disclaimers"],
    },
    "chaos_comedy": {
        "summary": "High-entropy narrative only when reward history proves it helps momentum.",
        "required_sections": REQUIRED_SECTIONS,
        "banned_behaviors": ["comedy without action", "style dominating intent", "inside joke replacing validation"],
    },
    "quiet_checkpoint": {
        "summary": "Low-stimulation repair mode after failed loops. Name the snag and reset the next action.",
        "required_sections": ["Operator read", "Blocked on", "Next mutation", "Validation"],
        "banned_behaviors": ["hype", "big architecture speech", "new surface before fixing the loop"],
    },
}


def build_operator_response_policy(
    root: Path,
    prompt: str = "",
    surface: str = "codex",
    context_pack: dict[str, Any] | None = None,
    inject: bool = False,
    write: bool = True,
) -> dict[str, Any]:
    """Build, persist, and optionally inject the active response policy."""
    root = Path(root)
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    context_pack = context_pack or {}
    prompt = str(prompt or context_pack.get("prompt") or "").strip()
    inputs = _load_policy_inputs(root, prompt, context_pack)
    selector = select_response_arm(root, prompt, context_pack=context_pack, inputs=inputs)
    active_arm = selector["selected_arm"]
    arm = RESPONSE_ARMS[active_arm]
    intent_moves = _extract_intent_moves(inputs)
    probe_files = _extract_probe_files(inputs, intent_moves)
    reward_summary = _reward_summary(inputs.get("style_model") or _default_style_model())

    policy = {
        "schema": POLICY_SCHEMA,
        "ts": _utc_now(),
        "surface": surface,
        "prompt_preview": _snip(prompt, 260),
        "operator_read": _operator_read(prompt, inputs, selector),
        "active_arm": active_arm,
        "selected_reason": selector.get("reason", ""),
        "response_arm": arm,
        "priority_order": PRIORITY_ORDER,
        "required_sections": list(arm.get("required_sections") or REQUIRED_SECTIONS),
        "default_response_shape": list(REQUIRED_SECTIONS),
        "banned_behaviors": _dedupe([
            *arm.get("banned_behaviors", []),
            "imitating operator typos unless quoting",
            "fake certainty about mutations not executed",
            "file quote when it does not carry signal",
        ]),
        "style_rules": [
            "Treat every answer as an action selected from context, rendered through policy, then scored by reward.",
            "Start by reading the real operator move, not by reciting architecture.",
            "Use intent graph/nodes and self-clearing files to choose what wakes up.",
            "Comedy is seasoning and signal, never the steering wheel.",
            "Sync conceptually with operator syntax and rhythm; do not intentionally reproduce typos unless quoting.",
        ],
        "intent_moves": intent_moves,
        "probe_files": probe_files,
        "next_mutation": _next_mutation(prompt, intent_moves, probe_files, selector),
        "file_quote_policy": "One short high-comedy line only when it carries state, conflict, or next-action signal.",
        "reward_weights": dict(REWARD_WEIGHTS),
        "recent_reward": reward_summary,
        "read_sources": {
            "prompt_brain": bool(inputs.get("prompt_brain")),
            "intent_graph": bool(inputs.get("intent_graph")),
            "intent_nodes": bool(inputs.get("intent_nodes")),
            "self_clearing_context_window": bool(inputs.get("self_clearing_context_window")),
            "file_mail_memory": bool(inputs.get("file_mail_memory")),
            "recent_reward_history": bool(inputs.get("style_model")),
        },
        "response_logging_contract": {
            "required_fields": [
                "response_id",
                "style_arm",
                "intent_nodes",
                "hook_ids",
                "context_window_files",
                "reward_features",
            ],
        },
        "engagement_hook_contract": {
            "required_fields": [
                "hook_id",
                "hook_type",
                "intensity",
                "target_intent_node",
                "expected_operator_action",
            ],
        },
        "paths": {
            "policy_json": "logs/operator_response_policy.json",
            "policy_markdown": "logs/operator_response_policy.md",
            "reward_events": "logs/response_reward_events.jsonl",
            "style_model": "logs/response_style_model.json",
            "copilot_instructions": ".github/copilot-instructions.md",
        },
    }
    if write:
        _write_json(logs / "operator_response_policy.json", policy)
        (logs / "operator_response_policy.md").write_text(render_operator_response_policy(policy) + "\n", encoding="utf-8")
    if inject:
        policy["injected"] = inject_operator_response_policy(root, policy)
        if write:
            _write_json(logs / "operator_response_policy.json", policy)
    return policy


def load_operator_response_policy(root: Path, max_age_minutes: int = 60) -> dict[str, Any]:
    """Load latest policy and mark it stale instead of silently trusting it."""
    root = Path(root)
    policy = _load_json(root / "logs" / "operator_response_policy.json") or {}
    if not policy:
        return {}
    age = _age_minutes(str(policy.get("ts") or ""))
    stale = age is None or age > max_age_minutes
    policy["stale"] = bool(stale)
    policy["stale_reason"] = "missing_or_old_policy_ts" if stale else ""
    policy["age_minutes"] = round(age, 2) if age is not None else None
    return policy


def render_operator_response_policy(policy: dict[str, Any], managed: bool = False) -> str:
    """Render a compact managed block for Copilot/Codex instructions."""
    arm = str(policy.get("active_arm") or "probe_council")
    lines: list[str] = []
    if managed:
        lines.append(POLICY_START)
    lines.extend([
        "## Operator Response Policy",
        "",
        f"ACTIVE_ARM: `{arm}`",
        f"POLICY_TS: `{policy.get('ts', '')}`",
        f"OPERATOR_READ: {_ascii(_snip(policy.get('operator_read'), 220))}",
        f"PRIORITY: {' > '.join(policy.get('priority_order') or PRIORITY_ORDER)}",
        "",
        "REQUIRED_RESPONSE_SHAPE:",
    ])
    for idx, section in enumerate(policy.get("required_sections") or REQUIRED_SECTIONS, 1):
        lines.append(f"{idx}. {section}")
    lines.extend([
        "",
        "RESPONSE_RULES:",
        "- Act as the probe layer for intent, files, and validation.",
        "- Start with what the prompt is really trying to do.",
        "- Extract 3-5 intent moves when the prompt contains multiple moves.",
        "- Name probe files from intent graph, intent nodes, and self-clearing context.",
        "- Propose a bounded next mutation or explicitly refuse to mutate.",
        "- Add exactly one file quote only when it carries useful state.",
        "- Do not imitate typos unless quoting the operator.",
        "",
        "BANNED_BEHAVIORS:",
    ])
    for item in policy.get("banned_behaviors") or []:
        lines.append(f"- {item}")
    lines.extend([
        "",
        "ACTIVE_INTENT_MOVES:",
    ])
    for move in (policy.get("intent_moves") or [])[:5]:
        lines.append(f"- `{_ascii(move.get('intent_key', 'none'))}` :: {_ascii(move.get('why', ''))}")
    if not policy.get("intent_moves"):
        lines.append("- none")
    lines.extend([
        "",
        "PROBE_FILES:",
    ])
    for item in (policy.get("probe_files") or [])[:8]:
        lines.append(f"- `{_ascii(item.get('file'))}` via {_ascii(item.get('reason', 'policy'))}")
    if not policy.get("probe_files"):
        lines.append("- none")
    reward = policy.get("recent_reward") if isinstance(policy.get("recent_reward"), dict) else {}
    lines.extend([
        "",
        f"RECENT_REWARD: arm `{reward.get('top_arm', 'none')}`, score `{reward.get('top_score', 0)}`",
        f"NEXT_MUTATION: {_ascii(_snip(policy.get('next_mutation'), 220))}",
    ])
    if policy.get("stale"):
        lines.extend([
            "",
            "STALE_POLICY_WARNING: latest policy is stale; rebuild before relying on it.",
        ])
    if managed:
        lines.append(POLICY_END)
    return "\n".join(lines)


def inject_operator_response_policy(root: Path, policy: dict[str, Any]) -> bool:
    root = Path(root)
    path = root / ".github" / "copilot-instructions.md"
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    if POLICY_START in text and POLICY_END not in text:
        text = text.rstrip() + "\n\n<!-- codex:operator-response-policy-stale missing-end -->\n"
    block = render_operator_response_policy(policy, managed=True)
    pattern = re.compile(re.escape(POLICY_START) + r".*?" + re.escape(POLICY_END), re.DOTALL)
    if pattern.search(text):
        updated = pattern.sub(lambda _match: block, text)
    else:
        updated = text.rstrip() + "\n\n" + block + "\n"
    if updated != text:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(updated, encoding="utf-8")
    return True


def select_response_arm(
    root: Path,
    prompt: str,
    context_pack: dict[str, Any] | None = None,
    inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(root)
    inputs = inputs or _load_policy_inputs(root, prompt, context_pack or {})
    model = inputs.get("style_model") or load_response_style_model(root)
    lower = str(prompt or "").lower()
    requested_comedy = any(bit in lower for bit in ("comedy", "crank entropy", "chaos", "file quote", "unhinged"))
    requested_mail = any(bit in lower for bit in ("email", "mail", "message thread", "old friend"))
    requested_patch = any(bit in lower for bit in ("implement", "patch", "fix", "test", "audit", "validate", "mutation"))
    failed_loop = any(bit in lower for bit in ("wrong", "not working", "terrible", "stale", "failed", "broken"))

    if requested_comedy and _chaos_allowed(model):
        return {"selected_arm": "chaos_comedy", "reason": "operator requested comedy and reward model says it preserves momentum"}
    if requested_comedy and not _chaos_allowed(model):
        if requested_patch:
            return {"selected_arm": "surgical_engineer", "reason": "comedy requested but chaos arm lacks thinking-momentum reward"}
        return {"selected_arm": "probe_council", "reason": "comedy requested but policy guard kept intent-first response"}
    if failed_loop:
        return {"selected_arm": "quiet_checkpoint", "reason": "recent prompt indicates a failed loop or stale surface"}
    if requested_patch:
        return {"selected_arm": "surgical_engineer", "reason": "prompt asks for implementation, audit, or validation"}
    if requested_mail:
        return {"selected_arm": "old_friend_file_mail", "reason": "prompt centers email/file memory interface"}

    best = _best_reward_arm(model)
    if best and best["count"] >= 2 and best["score"] > 0.62:
        if best["arm"] == "chaos_comedy" and not _chaos_allowed(model):
            return {"selected_arm": "probe_council", "reason": "chaos arm scored high but thinking momentum guard blocked it"}
        return {"selected_arm": best["arm"], "reason": "recent reward history favors this response arm"}
    return {"selected_arm": "probe_council", "reason": "default intent-first response arm"}


def load_response_style_model(root: Path) -> dict[str, Any]:
    root = Path(root)
    model = _load_json(root / "logs" / "response_style_model.json")
    if isinstance(model, dict) and model.get("schema") == STYLE_MODEL_SCHEMA:
        model.setdefault("arms", {})
        for arm in RESPONSE_ARMS:
            model["arms"].setdefault(arm, _empty_arm_stats())
        model.setdefault("style_notes", [])
        model.setdefault("avoid_rules", [])
        return model
    return _default_style_model()


def record_response_reward(root: Path, event: dict[str, Any], write: bool = True) -> dict[str, Any]:
    """Append a reward event and update the weighted style model."""
    root = Path(root)
    model = load_response_style_model(root)
    arm = str(event.get("style_arm") or event.get("active_arm") or "probe_council")
    if arm not in RESPONSE_ARMS:
        arm = "probe_council"
    feedback = str(event.get("feedback_text") or event.get("operator_feedback") or event.get("feedback") or "")
    response = str(event.get("response") or "")
    prompt = str(event.get("prompt") or "")
    explicit = _parse_explicit_feedback(feedback)
    passive = score_passive_reward(root, {
        "prompt": prompt,
        "response": response,
        "style_arm": arm,
        "intent_nodes": event.get("intent_nodes", []),
        "context_window_files": event.get("context_window_files", []),
        "reward_features": event.get("reward_features", {}),
    })
    dimension_scores = _merge_dimension_scores(passive["dimension_scores"], explicit["dimension_deltas"])
    weighted = _weighted_score(dimension_scores)
    score = _clamp(weighted + explicit["score_delta"], -1.0, 2.0)
    reward_event = {
        "schema": REWARD_EVENT_SCHEMA,
        "ts": event.get("ts") or _utc_now(),
        "response_id": event.get("response_id") or _response_id(prompt, response),
        "style_arm": arm,
        "intent_nodes": list(event.get("intent_nodes") or []),
        "hook_ids": list(event.get("hook_ids") or []),
        "context_window_files": list(event.get("context_window_files") or []),
        "explicit_feedback": explicit,
        "passive_reward": passive,
        "dimension_scores": dimension_scores,
        "weighted_score": round(weighted, 4),
        "score": round(score, 4),
        "reward_features": event.get("reward_features", {}),
    }
    _update_style_model(model, reward_event)
    if explicit["style_notes"]:
        model["style_notes"] = _dedupe([*model.get("style_notes", []), *explicit["style_notes"]])[-40:]
    if explicit["avoid_rules"]:
        model["avoid_rules"] = _dedupe([*model.get("avoid_rules", []), *explicit["avoid_rules"]])[-40:]
    model["updated_at"] = reward_event["ts"]
    if write:
        logs = root / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        _append_jsonl(logs / "response_reward_events.jsonl", reward_event)
        _write_json(logs / "response_style_model.json", model)
    reward_event["style_model"] = _reward_summary(model)
    return reward_event


def score_passive_reward(root: Path, event: dict[str, Any]) -> dict[str, Any]:
    """Score passive features without needing explicit feedback."""
    response = str(event.get("response") or "")
    prompt = str(event.get("prompt") or "")
    lower_response = response.lower()
    lower_prompt = prompt.lower()
    has_sections = sum(1 for section in REQUIRED_SECTIONS if section.lower() in lower_response)
    intent_refs = len(event.get("intent_nodes") or []) + len(re.findall(r"[a-z0-9_/.-]+:[a-z_]+:[a-z0-9_]+:[a-z_]+", response, flags=re.I))
    file_refs = len(event.get("context_window_files") or []) + len(re.findall(r"(?:src|client|logs|tests?)/[a-zA-Z0-9_./-]+", response))
    action_terms = sum(1 for bit in ("patch", "test", "run", "verify", "write", "mutate", "implement", "bounded") if bit in lower_response)
    comedy_terms = sum(1 for bit in ("quote", "gossip", "beef", "old friend", "side-eye", "comedy") if bit in lower_response)
    operator_specific = any(bit in lower_response for bit in ("operator read", "nikita", "intent moves", "probe files"))
    prompt_specific = bool(prompt and any(word in lower_response for word in _keywords(prompt)[:8]))
    loop_closure = any(bit in lower_response for bit in ("passed", "verified", "closed", "completion", "validated"))

    dimensions = {
        "thinking_momentum": _clamp(0.25 + 0.12 * has_sections + (0.18 if operator_specific else 0) + (0.12 if prompt_specific else 0), 0, 1),
        "intent_extraction_accuracy": _clamp(0.2 + min(intent_refs, 5) * 0.14 + (0.1 if "intent" in lower_prompt else 0), 0, 1),
        "code_mutation_readiness": _clamp(0.15 + min(file_refs, 6) * 0.08 + min(action_terms, 6) * 0.08 + (0.12 if loop_closure else 0), 0, 1),
        "comedy_style_resonance": _clamp(0.08 + min(comedy_terms, 4) * 0.12, 0, 1),
    }
    return {
        "schema": "passive_response_reward/v1",
        "ts": _utc_now(),
        "features": {
            "required_sections_present": has_sections,
            "intent_refs": intent_refs,
            "file_refs": file_refs,
            "action_terms": action_terms,
            "comedy_terms": comedy_terms,
            "operator_specific": operator_specific,
            "prompt_specific": prompt_specific,
            "loop_closure": loop_closure,
        },
        "dimension_scores": {key: round(value, 4) for key, value in dimensions.items()},
        "weighted_score": _weighted_score(dimensions),
    }


def response_log_defaults(
    root: Path,
    prompt: str = "",
    response: str = "",
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(root)
    policy = policy or load_operator_response_policy(root) or build_operator_response_policy(root, prompt, write=True, inject=False)
    intent_nodes = [
        str(move.get("intent_key") or move.get("node_id") or "")
        for move in (policy.get("intent_moves") or [])[:5]
        if move.get("intent_key") or move.get("node_id")
    ]
    hooks = _load_json(root / "logs" / "engagement_hooks_latest.json") or {}
    hook_ids = [
        str(item.get("hook_id"))
        for item in (hooks.get("hooks") or [])
        if isinstance(item, dict) and item.get("hook_id")
    ]
    files = [
        str(item.get("file"))
        for item in (policy.get("probe_files") or [])
        if isinstance(item, dict) and item.get("file")
    ]
    passive = score_passive_reward(root, {
        "prompt": prompt,
        "response": response,
        "intent_nodes": intent_nodes,
        "context_window_files": files,
    })
    return {
        "style_arm": policy.get("active_arm") or "probe_council",
        "intent_nodes": intent_nodes,
        "hook_ids": hook_ids,
        "context_window_files": files,
        "reward_features": passive.get("features", {}),
    }


def _load_policy_inputs(root: Path, prompt: str, context_pack: dict[str, Any]) -> dict[str, Any]:
    logs = root / "logs"
    prompt_brain = context_pack.get("prompt_brain") or _load_json(logs / "prompt_brain_latest.json") or {}
    intent_graph = (
        context_pack.get("intent_graph")
        or prompt_brain.get("intent_graph")
        or _load_json(logs / "intent_graph_latest.json")
        or {}
    )
    if prompt and not intent_graph:
        try:
            from src.tc_intent_keys_seq001_v001 import generate_intent_graph
            signals = context_pack.get("signals") if isinstance(context_pack.get("signals"), dict) else {}
            intent_graph = generate_intent_graph(
                root,
                prompt,
                deleted_words=signals.get("deleted_words") or [],
                context_selection=context_pack.get("context_selection") if isinstance(context_pack.get("context_selection"), dict) else None,
                write=True,
            )
        except Exception as exc:
            intent_graph = {"status": "error", "error": str(exc)}
    clearing = intent_graph.get("context_clearing_pass") if isinstance(intent_graph, dict) else {}
    intent_nodes = (
        intent_graph.get("intent_nodes")
        if isinstance(intent_graph.get("intent_nodes"), dict)
        else _load_json(logs / "intent_nodes_latest.json") or {}
    )
    return {
        "prompt_brain": prompt_brain,
        "intent_graph": intent_graph,
        "intent_nodes": intent_nodes,
        "self_clearing_context_window": clearing or {},
        "file_mail_memory": _load_json(logs / "file_memory_index.json") or _load_json(logs / "file_memory_latest.json") or {},
        "style_model": load_response_style_model(root),
        "context_pack": context_pack,
    }


def _extract_intent_moves(inputs: dict[str, Any]) -> list[dict[str, Any]]:
    graph = inputs.get("intent_graph") if isinstance(inputs.get("intent_graph"), dict) else {}
    moves = []
    for item in (graph.get("intents") or [])[:5]:
        if not isinstance(item, dict):
            continue
        moves.append({
            "intent_key": item.get("intent_key", ""),
            "scope": item.get("scope", ""),
            "verb": item.get("verb", ""),
            "target": item.get("target", ""),
            "confidence": item.get("confidence", 0),
            "files": item.get("files", [])[:6] if isinstance(item.get("files"), list) else [],
            "why": item.get("why") or _snip(item.get("segment"), 160),
        })
    if moves:
        return moves
    brain = inputs.get("prompt_brain") if isinstance(inputs.get("prompt_brain"), dict) else {}
    if brain.get("intent_key"):
        return [{
            "intent_key": brain.get("intent_key"),
            "scope": brain.get("scope", ""),
            "verb": brain.get("verb", ""),
            "target": brain.get("target", ""),
            "confidence": brain.get("confidence", 0),
            "files": [],
            "why": "prompt brain latest intent key",
        }]
    return []


def _extract_probe_files(inputs: dict[str, Any], intent_moves: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for move in intent_moves:
        for file_path in move.get("files") or []:
            out.append({"file": str(file_path), "reason": f"intent:{move.get('verb') or 'route'}"})
    clearing = inputs.get("self_clearing_context_window") if isinstance(inputs.get("self_clearing_context_window"), dict) else {}
    for item in clearing.get("selected_files") or []:
        if isinstance(item, dict):
            out.append({
                "file": str(item.get("file") or ""),
                "score": item.get("final_score"),
                "reason": "self_clearing_context_window",
            })
    pack = inputs.get("context_pack") if isinstance(inputs.get("context_pack"), dict) else {}
    for item in pack.get("focus_files") or []:
        if isinstance(item, dict):
            out.append({
                "file": str(item.get("path") or item.get("file") or item.get("name") or ""),
                "score": item.get("score"),
                "reason": item.get("reason") or "focus_files",
            })
    context = pack.get("context_selection") if isinstance(pack.get("context_selection"), dict) else {}
    for item in context.get("files") or []:
        if isinstance(item, dict):
            out.append({
                "file": str(item.get("path") or item.get("file") or item.get("name") or ""),
                "score": item.get("score"),
                "reason": "numeric_context",
            })
    return _dedupe_files(out)[:10]


def _operator_read(prompt: str, inputs: dict[str, Any], selector: dict[str, Any]) -> str:
    lower = str(prompt or "").lower()
    if "reward" in lower and ("style" in lower or "response" in lower):
        return "Build a persistent response policy and reward loop so the assistant surface adapts to operator momentum."
    if "email" in lower or "mail" in lower:
        return "Unify file mail with the live operator policy so messages become useful memory, not notifications."
    if "intent" in lower and ("graph" in lower or "node" in lower):
        return "Use structured intent extraction and intent-node memory to wake the right files before the model answers."
    if any(bit in lower for bit in ("implement", "patch", "fix", "test", "audit")):
        return "Mutate the repo through a bounded patch, then prove it with tests or a clear validation gate."
    if selector.get("selected_arm") == "quiet_checkpoint":
        return "Reset a failed or stale loop by naming the snag and choosing one concrete next action."
    return "Extract the real move, pick the files that should wake, and produce an action-ready response."


def _next_mutation(prompt: str, moves: list[dict[str, Any]], files: list[dict[str, Any]], selector: dict[str, Any]) -> str:
    if selector.get("selected_arm") == "quiet_checkpoint":
        return "Do not expand scope; identify the failed loop and patch the smallest verified path."
    if files:
        first = files[0]["file"]
        return f"Load `{first}` with the top intent move and propose one bounded patch plus validation."
    if moves:
        return f"Resolve context for `{moves[0].get('intent_key')}` before mutating source."
    if prompt:
        return "Compile the prompt into intent moves, then select files before source mutation."
    return "No mutation until a prompt, intent node, or context file wakes."


def _parse_explicit_feedback(text: str) -> dict[str, Any]:
    lower = str(text or "").lower()
    score_delta = 0.0
    explicit_rewards = []
    for match in re.findall(r"reward\s*:\s*([+-]?\d+(?:\.\d+)?)", lower):
        try:
            value = float(match)
        except ValueError:
            continue
        explicit_rewards.append(value)
        score_delta += value * 0.18
    phrase_deltas = {
        "again": 0.16,
        "letsgooo": 0.24,
        "that's it": 0.24,
        "thats it": 0.24,
        "more actionable": 0.16,
        "not working": -0.28,
        "wrong": -0.28,
        "boring": -0.18,
        "too chatgpt": -0.28,
        "less structure": -0.08,
        "crank entropy": 0.08,
    }
    matched = []
    for phrase, delta in phrase_deltas.items():
        if phrase in lower:
            matched.append(phrase)
            score_delta += delta
    style_notes = _command_values(text, "style")
    avoid_rules = _command_values(text, "avoid")
    dimension_deltas = {
        "thinking_momentum": 0.0,
        "intent_extraction_accuracy": 0.0,
        "code_mutation_readiness": 0.0,
        "comedy_style_resonance": 0.0,
    }
    if any(bit in matched for bit in ("again", "letsgooo", "that's it", "thats it")):
        dimension_deltas["thinking_momentum"] += 0.18
    if "more actionable" in matched:
        dimension_deltas["code_mutation_readiness"] += 0.16
    if "crank entropy" in matched:
        dimension_deltas["comedy_style_resonance"] += 0.18
    if any(bit in matched for bit in ("too chatgpt", "boring")):
        dimension_deltas["comedy_style_resonance"] -= 0.18
        dimension_deltas["thinking_momentum"] -= 0.08
    if any(bit in matched for bit in ("wrong", "not working")):
        dimension_deltas["intent_extraction_accuracy"] -= 0.22
        dimension_deltas["code_mutation_readiness"] -= 0.12
    return {
        "raw": text,
        "explicit_rewards": explicit_rewards,
        "matched_phrases": matched,
        "score_delta": round(score_delta, 4),
        "dimension_deltas": dimension_deltas,
        "style_notes": style_notes,
        "avoid_rules": avoid_rules,
    }


def _update_style_model(model: dict[str, Any], reward_event: dict[str, Any]) -> None:
    arm = reward_event["style_arm"]
    arms = model.setdefault("arms", {})
    stats = arms.setdefault(arm, _empty_arm_stats())
    stats["count"] = int(stats.get("count") or 0) + 1
    stats["reward_total"] = round(float(stats.get("reward_total") or 0.0) + float(reward_event.get("score") or 0.0), 4)
    stats["score"] = round(float(stats["reward_total"]) / max(1, int(stats["count"])), 4)
    stats["last_reward_ts"] = reward_event.get("ts", "")
    dims = stats.setdefault("dimension_scores", {})
    for key, value in (reward_event.get("dimension_scores") or {}).items():
        old = float(dims.get(key, 0.0) or 0.0)
        dims[key] = round(old * 0.65 + float(value) * 0.35, 4)
    stats["last_event"] = {
        "response_id": reward_event.get("response_id"),
        "score": reward_event.get("score"),
        "hook_ids": reward_event.get("hook_ids", []),
    }


def _merge_dimension_scores(base: dict[str, Any], deltas: dict[str, Any]) -> dict[str, float]:
    merged = {}
    for key in REWARD_WEIGHTS:
        merged[key] = round(_clamp(float(base.get(key) or 0.0) + float(deltas.get(key) or 0.0), 0, 1), 4)
    return merged


def _weighted_score(dimensions: dict[str, Any]) -> float:
    total = 0.0
    for key, weight in REWARD_WEIGHTS.items():
        total += float(dimensions.get(key) or 0.0) * weight
    return round(total, 4)


def _default_style_model() -> dict[str, Any]:
    return {
        "schema": STYLE_MODEL_SCHEMA,
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
        "reward_weights": dict(REWARD_WEIGHTS),
        "arms": {arm: _empty_arm_stats() for arm in RESPONSE_ARMS},
        "style_notes": [],
        "avoid_rules": [],
    }


def _empty_arm_stats() -> dict[str, Any]:
    return {
        "count": 0,
        "reward_total": 0.0,
        "score": 0.0,
        "dimension_scores": {key: 0.0 for key in REWARD_WEIGHTS},
        "last_reward_ts": "",
    }


def _reward_summary(model: dict[str, Any]) -> dict[str, Any]:
    best = _best_reward_arm(model)
    return {
        "top_arm": best["arm"] if best else "none",
        "top_score": best["score"] if best else 0,
        "top_count": best["count"] if best else 0,
        "style_notes": (model.get("style_notes") or [])[-5:],
        "avoid_rules": (model.get("avoid_rules") or [])[-5:],
    }


def _best_reward_arm(model: dict[str, Any]) -> dict[str, Any] | None:
    arms = model.get("arms") if isinstance(model.get("arms"), dict) else {}
    rows = []
    for arm, stats in arms.items():
        if arm not in RESPONSE_ARMS or not isinstance(stats, dict):
            continue
        rows.append({
            "arm": arm,
            "score": float(stats.get("score") or 0.0),
            "count": int(stats.get("count") or 0),
        })
    if not rows:
        return None
    rows.sort(key=lambda item: (item["score"], item["count"]), reverse=True)
    return rows[0]


def _chaos_allowed(model: dict[str, Any]) -> bool:
    stats = ((model.get("arms") or {}).get("chaos_comedy") or {}) if isinstance(model, dict) else {}
    count = int(stats.get("count") or 0)
    dims = stats.get("dimension_scores") if isinstance(stats.get("dimension_scores"), dict) else {}
    thinking = float(dims.get("thinking_momentum") or 0.0)
    mutation = float(dims.get("code_mutation_readiness") or 0.0)
    score = float(stats.get("score") or 0.0)
    return count >= 2 and score >= 0.5 and thinking >= 0.45 and mutation >= 0.25


def _command_values(text: str, command: str) -> list[str]:
    values = []
    pattern = re.compile(rf"^\s*{re.escape(command)}\s*:\s*(.+?)\s*$", re.I | re.M)
    for match in pattern.finditer(str(text or "")):
        value = match.group(1).strip()
        if value:
            values.append(value[:240])
    return values


def _keywords(text: str) -> list[str]:
    stop = {"the", "and", "for", "with", "that", "this", "from", "into", "should", "would", "could"}
    words = [word.lower() for word in re.findall(r"[a-zA-Z][a-zA-Z0-9_]+", str(text or ""))]
    return [word for word in words if len(word) > 3 and word not in stop]


def _dedupe(values: list[Any]) -> list[Any]:
    out = []
    seen = set()
    for item in values:
        key = json.dumps(item, sort_keys=True, ensure_ascii=False) if isinstance(item, (dict, list)) else str(item)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def _dedupe_files(values: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    seen = set()
    for item in values:
        file_path = str(item.get("file") or "").replace("\\", "/").strip()
        if not file_path or file_path in seen:
            continue
        seen.add(file_path)
        new_item = dict(item)
        new_item["file"] = file_path
        out.append(new_item)
    return out


def _snip(value: Any, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) > limit:
        return text[: max(0, limit - 3)].rstrip() + "..."
    return text


def _ascii(value: Any) -> str:
    return str(value or "").encode("ascii", errors="replace").decode("ascii")


def _response_id(prompt: str, response: str) -> str:
    digest = hashlib.sha256(f"{prompt}|{response}|{_utc_now()}".encode("utf-8")).hexdigest()[:16]
    return f"response:{digest}"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _age_minutes(ts: str) -> float | None:
    try:
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - parsed).total_seconds() / 60
    except Exception:
        return None


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
