"""Compile operator intent across prompt history and diagnose why the repo is not yet self-healing."""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "operator_intent_compiler/v1"

INTENT_BUCKETS = {
    "repo_self_healing": [
        "self heal", "self-heal", "self healing", "self-healing", "alive", "autonomous",
        "auto fix", "easy fixes", "overwrite", "rewrite", "mutation", "interlinked",
    ],
    "intent_compilation": [
        "intent", "intent key", "intent graph", "intent node", "compile", "hyper intent",
        "numeric", "neumeric", "encoding", "semantic",
    ],
    "thought_completion": [
        "thought completer", "thought composer", "pause", "hesitation", "unsaid",
        "you were gonna say", "popup", "completion",
    ],
    "file_sim_orchestration": [
        "file sim", "sims", "simulation", "file combinations", "context pack", "job",
        "council", "grader", "10q", "consensus",
    ],
    "file_mail_memory": [
        "email", "mail", "resend", "old friend", "file quote", "messages", "memory",
        "context@myaifingerprint",
    ],
    "copilot_codex_interface": [
        "copilot", "codex", "prompt box", "inject", "response format", "style",
        "interface", "hooks",
    ],
    "repo_boundary_pressure": [
        "split", "different projects", "separate", "linkrouter", "maif", "maid",
        "closed", "sensitive", "leak",
    ],
    "dead_stale_cleanup": [
        "dead", "stale", "killed", "mutated", "audit", "cleanup", "orphan",
    ],
    "model_routing": [
        "deepseek", "gemini", "grok", "claude", "model", "grader model",
    ],
}


def compile_operator_intent(root: Path, prompt_limit: int = 888, write: bool = True) -> dict[str, Any]:
    root = Path(root)
    logs = root / "logs"
    prompts = _load_jsonl(logs / "prompt_journal.jsonl")[-prompt_limit:]
    compositions = _load_jsonl(logs / "chat_compositions.jsonl")[-prompt_limit:]
    prompt_texts = [str(row.get("msg") or row.get("final_text") or "") for row in prompts]
    composition_texts = [str(row.get("final_text") or "") for row in compositions]
    all_text = "\n".join([*prompt_texts, *composition_texts])
    bucket_hits = _bucket_hits([*prompt_texts, *composition_texts])
    top_terms = _top_terms(all_text)
    prompt_counts = Counter(str(row.get("intent") or "unknown") for row in prompts)
    state_counts = Counter(
        str(row.get("cognitive_state") or ((row.get("chat_state") or {}).get("state")) or "unknown")
        for row in prompts
    )
    deletion = _deletion_summary(prompts, compositions)
    runtime = _runtime_state(root)
    blockers = _alive_blockers(root, runtime, len(prompts), prompt_limit)
    split = _split_pressure(bucket_hits, blockers)
    report = {
        "schema": SCHEMA,
        "ts": _now(),
        "requested_prompt_count": prompt_limit,
        "available_prompt_count": len(prompts),
        "available_composition_count": len(compositions),
        "coverage_gap": max(0, prompt_limit - len(prompts)),
        "prompt_intent_counts": dict(prompt_counts),
        "cognitive_state_counts": dict(state_counts),
        "bucket_hits": bucket_hits,
        "top_terms": top_terms,
        "deletion_summary": deletion,
        "runtime_state": runtime,
        "missing_alive_loop": blockers,
        "split_pressure": split,
        "compiled_read": _compiled_read(bucket_hits, blockers, len(prompts), prompt_limit),
        "next_actions": _next_actions(blockers),
        "paths": {
            "json": "logs/operator_intent_888.json",
            "markdown": "logs/operator_intent_888.md",
        },
    }
    if write:
        logs.mkdir(parents=True, exist_ok=True)
        _write_json(logs / "operator_intent_888.json", report)
        (logs / "operator_intent_888.md").write_text(render_operator_intent_report(report), encoding="utf-8")
    return report


def render_operator_intent_report(report: dict[str, Any]) -> str:
    runtime = report.get("runtime_state") if isinstance(report.get("runtime_state"), dict) else {}
    lines = [
        "# Operator Intent Compile - 888 Prompt Target",
        "",
        f"- generated_at: `{report.get('ts', '')}`",
        f"- requested_prompts: `{report.get('requested_prompt_count', 0)}`",
        f"- available_prompt_rows: `{report.get('available_prompt_count', 0)}`",
        f"- available_composition_rows: `{report.get('available_composition_count', 0)}`",
        f"- coverage_gap: `{report.get('coverage_gap', 0)}`",
        "",
        "## Operator Read",
        "",
        report.get("compiled_read", ""),
        "",
        "## Dominant Intent Nodes",
        "",
    ]
    for bucket, data in sorted((report.get("bucket_hits") or {}).items(), key=lambda pair: pair[1]["hits"], reverse=True):
        lines.append(f"- `{bucket}` hits `{data.get('hits', 0)}`: {data.get('read', '')}")
    lines.extend([
        "",
        "## Why The Repo Is Not Alive Yet",
        "",
    ])
    for blocker in report.get("missing_alive_loop") or []:
        lines.extend([
            f"### {blocker.get('name')}",
            "",
            f"- severity: `{blocker.get('severity')}`",
            f"- evidence: {blocker.get('evidence')}",
            f"- why it matters: {blocker.get('why')}",
            f"- fix: {blocker.get('fix')}",
            "",
        ])
    lines.extend([
        "## Runtime Snapshot",
        "",
        f"- latest_context_confidence: `{runtime.get('context_confidence')}`",
        f"- latest_stale_blocks: `{', '.join(runtime.get('stale_blocks') or []) or 'none'}`",
        f"- latest_loop_status: `{runtime.get('intent_loop_status')}`",
        f"- latest_loop_stage: `{runtime.get('intent_loop_stage')}`",
        f"- latest_observed_edits: `{runtime.get('observed_edits')}`",
        f"- latest_observed_responses: `{runtime.get('observed_responses')}`",
        f"- response_reward_events: `{runtime.get('response_reward_events')}`",
        f"- dirty_files_seen_by_sim: `{runtime.get('dirty_files_seen_by_sim')}`",
        f"- dead_stale_findings: `{runtime.get('dead_stale_findings')}`",
        "",
        "## Split Pressure",
        "",
    ])
    split = report.get("split_pressure") if isinstance(report.get("split_pressure"), dict) else {}
    lines.extend([
        f"- risk: `{split.get('risk')}`",
        f"- read: {split.get('read')}",
        f"- keep together if: {split.get('keep_together_if')}",
        f"- split if: {split.get('split_if')}",
        "",
        "## Next Actions",
        "",
    ])
    for action in report.get("next_actions") or []:
        lines.append(f"- {action}")
    lines.extend([
        "",
        "## Top Terms",
        "",
        "- " + ", ".join(report.get("top_terms") or []),
        "",
    ])
    return "\n".join(lines)


def _bucket_hits(texts: list[str]) -> dict[str, dict[str, Any]]:
    joined = "\n".join(texts).lower()
    out = {}
    reads = {
        "repo_self_healing": "You want source to organize into validated, operator-aligned fixes without constant manual steering.",
        "intent_compilation": "Intent keys/numeric encoding are supposed to be the routing math, not decorative metadata.",
        "thought_completion": "Pause/unsaid capture should become a planning signal before prompts hit the model.",
        "file_sim_orchestration": "File sims should form jobs, context packs, validation gates, and backward learning packets.",
        "file_mail_memory": "Email should be memory/control surface, not notification confetti.",
        "copilot_codex_interface": "Copilot/Codex should act as probes/executors reading the same policy and intent state.",
        "repo_boundary_pressure": "The repo is under pressure because product surfaces and private external repos are bleeding into one context space.",
        "dead_stale_cleanup": "Dead/stale code needs to feed deranking and cleanup, not just sit in a report.",
        "model_routing": "Fast proposal, grader, deep rewrite, and validation model roles need firm contracts.",
    }
    for bucket, phrases in INTENT_BUCKETS.items():
        hits = 0
        examples = []
        for phrase in phrases:
            count = joined.count(phrase)
            hits += count
            if count:
                examples.append(phrase)
        out[bucket] = {
            "hits": hits,
            "matched_phrases": examples[:12],
            "read": reads[bucket],
        }
    return out


def _alive_blockers(root: Path, runtime: dict[str, Any], available_prompts: int, requested: int) -> list[dict[str, Any]]:
    blockers = []
    if available_prompts < requested:
        blockers.append({
            "name": "capture_retention_gap",
            "severity": "P0",
            "evidence": f"requested {requested} prompts but prompt_journal has {available_prompts}",
            "why": "The operator model cannot become scary accurate if older prompt state is not retained or imported.",
            "fix": "Import historical sessions or consolidate prompt logs into one append-only operator memory store.",
        })
    if not runtime.get("response_reward_events"):
        blockers.append({
            "name": "reward_loop_not_firing",
            "severity": "P0",
            "evidence": "logs/response_reward_events.jsonl is missing or empty",
            "why": "Response style and hook quality cannot adapt without explicit/passive reward events.",
            "fix": "Call log_response after each assistant/Copilot answer and attach reward/style feedback to the response_id.",
        })
    confidence = runtime.get("context_confidence")
    if confidence is None or confidence < 0.2:
        blockers.append({
            "name": "context_selection_too_weak",
            "severity": "P0",
            "evidence": f"latest context confidence is {confidence}",
            "why": "Self-heal proposals wake weakly related files, so the system hesitates or picks stale surfaces.",
            "fix": "Train intent nodes with accepted edit pairs and use dead/stale audit to derank stale file identities.",
        })
    stale_blocks = runtime.get("stale_blocks") or []
    if stale_blocks:
        blockers.append({
            "name": "stale_context_blocks_still_in_prompt_path",
            "severity": "P1",
            "evidence": ", ".join(stale_blocks),
            "why": "A live repo cannot trust prompt injections when old blocks compete with fresh state.",
            "fix": "Make stale blocks hard-fail or mark them unusable in dynamic context selection.",
        })
    if runtime.get("intent_loop_status") == "awaiting_operator_approval" and runtime.get("observed_edits", 0) == 0:
        blockers.append({
            "name": "loop_has_no_execution_muscle",
            "severity": "P0",
            "evidence": "latest intent loop is awaiting approval with zero observed edits",
            "why": "The system compiles intent and proposals, but does not close human-to-Copilot-to-repo execution.",
            "fix": "Add an approved low-risk lane: apply only tiny patches with existing tests, then bind edit/validation back to the loop.",
        })
    if runtime.get("ten_q_null"):
        blockers.append({
            "name": "consensus_scores_missing",
            "severity": "P1",
            "evidence": "latest proposals have null ten_q_score / ten_q_passed",
            "why": "Deep rewrite and email guards depend on consensus, so null scores freeze autonomy.",
            "fix": "Score every proposal locally even when a model grader is unavailable; null should become fail-with-reason.",
        })
    if runtime.get("fake_tests_in_validation"):
        blockers.append({
            "name": "validation_plans_reference_missing_tests",
            "severity": "P1",
            "evidence": "latest validation plans include synthesized test filenames",
            "why": "A self-heal loop cannot move quickly if its own validation commands are imaginary.",
            "fix": "Map source files to real existing tests before proposing rewrites; otherwise use py_compile plus known integration tests.",
        })
    if runtime.get("dirty_files_seen_by_sim", 0) > 10:
        blockers.append({
            "name": "dirty_worktree_blocks_trust",
            "severity": "P1",
            "evidence": f"latest sim saw {runtime.get('dirty_files_seen_by_sim')} dirty files",
            "why": "Large unsubmitted work makes it hard to distinguish user edits, generated state, and self-heal patches.",
            "fix": "Batch current work into named intent submissions before enabling faster self-heal.",
        })
    if runtime.get("dead_stale_findings", 0) > 200:
        blockers.append({
            "name": "stale_file_identities_not_deranking",
            "severity": "P1",
            "evidence": f"dead/stale audit found {runtime.get('dead_stale_findings')} live suspects",
            "why": "Old identities still wake in sims, so the context window spends tokens on dead history.",
            "fix": "Feed dead_stale_code_findings into intent node/file sim scoring as negative evidence.",
        })
    if runtime.get("email_stale"):
        blockers.append({
            "name": "email_per_prompt_not_closed",
            "severity": "P2",
            "evidence": "file email outbox is older than latest prompt lifecycle state",
            "why": "Mail memory cannot be the operator control surface if prompts complete without a receipt.",
            "fix": "Emit submission/completion mail from intent loop transitions, not only from file sim proposals.",
        })
    return blockers


def _runtime_state(root: Path) -> dict[str, Any]:
    logs = root / "logs"
    context = _load_json(logs / "context_selection.json") or {}
    sim = _load_json(logs / "batch_rewrite_sim_latest.json") or {}
    loop = _load_json(logs / "intent_loop_latest.json") or {}
    stale = _load_json(logs / "dead_stale_code_audit_latest.json") or {}
    proposals = sim.get("proposals") if isinstance(sim.get("proposals"), list) else []
    validation = []
    for item in proposals:
        validation.extend(str(cmd) for cmd in item.get("validation_plan") or [])
    fake_tests = [
        cmd for cmd in validation
        if "pytest test_" in cmd and not _validation_test_exists(root, cmd)
    ]
    prompt_ts = _latest_ts(logs / "prompt_journal.jsonl")
    email_ts = _latest_ts(logs / "file_email_outbox.jsonl")
    return {
        "context_confidence": context.get("confidence"),
        "stale_blocks": context.get("stale_blocks") or ((sim.get("distributed_intent_encoding") or {}).get("stale_blocks") or []),
        "intent_loop_status": loop.get("status"),
        "intent_loop_stage": loop.get("stage"),
        "observed_edits": len(loop.get("observed_edits") or []),
        "observed_responses": len(loop.get("observed_responses") or []),
        "proposal_count": len(proposals),
        "ten_q_null": any(item.get("ten_q_score") is None or item.get("ten_q_passed") is None for item in proposals),
        "fake_tests_in_validation": bool(fake_tests),
        "fake_validation_commands": fake_tests[:6],
        "dirty_files_seen_by_sim": len((sim.get("self_model") or {}).get("dirty_files") or []),
        "self_model_avg_fix_rate": (sim.get("self_model") or {}).get("avg_fix_rate"),
        "dead_stale_findings": stale.get("findings_count", 0),
        "dead_stale_suspects": (stale.get("category_counts") or {}).get("stale_suspect", 0),
        "response_reward_events": _line_count(logs / "response_reward_events.jsonl"),
        "ai_responses": _line_count(logs / "ai_responses.jsonl"),
        "edit_pairs": _line_count(logs / "edit_pairs.jsonl"),
        "training_pairs": _line_count(logs / "training_pairs.jsonl"),
        "intent_graphs": _line_count(logs / "intent_graph_history.jsonl"),
        "file_sims": _line_count(logs / "batch_rewrite_sim.jsonl"),
        "intent_loops": _line_count(logs / "intent_loop_history.jsonl"),
        "file_emails": _line_count(logs / "file_email_outbox.jsonl"),
        "email_stale": bool(prompt_ts and email_ts and email_ts < prompt_ts),
        "latest_prompt_ts": prompt_ts.isoformat() if prompt_ts else "",
        "latest_email_ts": email_ts.isoformat() if email_ts else "",
    }


def _split_pressure(bucket_hits: dict[str, dict[str, Any]], blockers: list[dict[str, Any]]) -> dict[str, str]:
    boundary = bucket_hits.get("repo_boundary_pressure", {}).get("hits", 0)
    p0 = len([item for item in blockers if item.get("severity") == "P0"])
    if boundary >= 5 or p0 >= 3:
        risk = "high"
    elif boundary >= 2 or p0 >= 1:
        risk = "medium"
    else:
        risk = "low"
    return {
        "risk": risk,
        "read": "The repo should not be split because it is conceptually wrong; it should be split if shared memory cannot enforce boundaries.",
        "keep_together_if": "one orchestrator can isolate project scopes, derank stale identities, and run validation receipts per loop.",
        "split_if": "context selection keeps pulling closed/external repo identities into local work or self-heal cannot operate below project scope.",
    }


def _compiled_read(bucket_hits: dict[str, dict[str, Any]], blockers: list[dict[str, Any]], available: int, requested: int) -> str:
    top = sorted(bucket_hits.items(), key=lambda pair: pair[1]["hits"], reverse=True)[:4]
    names = ", ".join(name for name, _data in top)
    return (
        f"Across the available {available}/{requested} prompt rows, the dominant move is not just adding features. "
        f"It is building a closed-loop source organism around {names}. The repo is not alive yet because sensing "
        "is ahead of action: it logs, simulates, and proposes, but reward, validation, deranking, and approved mutation "
        "are not closing fast enough."
    )


def _next_actions(blockers: list[dict[str, Any]]) -> list[str]:
    priority = {
        "capture_retention_gap": "Unify prompt history: import older session logs or mark the 699 missing prompts as unrecoverable.",
        "reward_loop_not_firing": "Make every assistant/Copilot response call `log_response` so `response_reward_events.jsonl` starts growing.",
        "context_selection_too_weak": "Feed accepted edit pairs and dead/stale negative evidence into numeric/context selection.",
        "loop_has_no_execution_muscle": "Create a tiny approved self-heal lane: py_compile-only patches under one file, then bind edit and validation.",
        "consensus_scores_missing": "Replace null 10Q with deterministic local scores and fail reasons.",
        "validation_plans_reference_missing_tests": "Map validation plans to real test files before any rewrite can be approved.",
        "stale_file_identities_not_deranking": "Use `dead_stale_code_findings.jsonl` as derank input for file sims and intent nodes.",
        "email_per_prompt_not_closed": "Move email receipts onto intent-loop submission/completion transitions.",
    }
    actions = []
    seen = set()
    for blocker in blockers:
        name = blocker.get("name")
        if name in priority and name not in seen:
            seen.add(name)
            actions.append(priority[name])
    return actions[:8]


def _deletion_summary(prompts: list[dict[str, Any]], compositions: list[dict[str, Any]]) -> dict[str, Any]:
    words = []
    ratios = []
    for row in prompts:
        ratios.append(float(((row.get("signals") or {}).get("deletion_ratio")) or row.get("deletion_ratio") or 0))
        words.extend(str(item) for item in row.get("deleted_words") or [])
    for row in compositions:
        ratios.append(float(row.get("deletion_ratio") or 0))
        for item in row.get("deleted_words") or []:
            words.append(str(item.get("word") if isinstance(item, dict) else item))
        for item in row.get("intent_deleted_words") or []:
            words.append(str(item.get("word") if isinstance(item, dict) else item))
    return {
        "avg_deletion_ratio": round(sum(ratios) / max(1, len(ratios)), 4),
        "deleted_word_count": len([word for word in words if word.strip()]),
        "top_deleted_words": [word for word, _count in Counter(words).most_common(12) if word],
    }


def _top_terms(text: str, limit: int = 30) -> list[str]:
    stop = {
        "the", "and", "for", "with", "that", "this", "what", "want", "need", "you",
        "but", "not", "how", "can", "should", "would", "like", "from", "into",
    }
    words = [
        word.lower()
        for word in re.findall(r"[A-Za-z][A-Za-z0-9_]+", text)
        if len(word) > 3 and word.lower() not in stop
    ]
    return [word for word, _count in Counter(words).most_common(limit)]


def _validation_test_exists(root: Path, command: str) -> bool:
    match = re.search(r"pytest\s+([^\s]+)", command)
    if not match:
        return True
    candidate = root / match.group(1)
    return candidate.exists()


def _latest_ts(path: Path) -> datetime | None:
    rows = _load_jsonl(path)
    if not rows:
        data = _load_json(path)
        if not data:
            return None
        return _parse_ts(str(data.get("ts") or data.get("updated_at") or ""))
    row = rows[-1]
    return _parse_ts(str(row.get("ts") or row.get("updated_at") or ""))


def _parse_ts(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        return None


def _line_count(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        return len([line for line in path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()])
    except OSError:
        return 0


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    out = []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return []
    for line in lines:
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict):
            out.append(row)
    return out


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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    report = compile_operator_intent(Path.cwd(), prompt_limit=888, write=True)
    print(json.dumps({
        "schema": report["schema"],
        "available_prompt_count": report["available_prompt_count"],
        "coverage_gap": report["coverage_gap"],
        "blockers": [item["name"] for item in report["missing_alive_loop"]],
        "paths": report["paths"],
    }, indent=2, ensure_ascii=False))
