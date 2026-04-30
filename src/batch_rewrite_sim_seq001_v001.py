"""Proposal-only batch rewrite simulator.

Compiles the current/operator intent, learns a tiny deterministic self-model
from repo history and failure logs, then proposes rewrite batches with
approval, context-injection, and cross-file validation gates.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "batch_rewrite_sim/v1"
STOP = {
    "the", "and", "for", "with", "that", "this", "from", "into", "should",
    "would", "could", "have", "make", "work", "working", "actual", "using",
    "based", "time", "over", "all", "about", "then", "than",
}
VERBS = {
    "patch": {"fix", "patch", "bug", "repair", "self", "healing"},
    "build": {"build", "add", "wire", "implement", "create", "ship"},
    "refactor": {"rewrite", "rewrites", "refactor", "split", "migrate"},
    "validate": {"test", "validate", "check", "verify", "compile"},
    "route": {"intent", "orchestrator", "context", "inject", "routing"},
}
RISKY_SUFFIXES = {".json", ".jsonl", ".db", ".sqlite", ".pgd"}
RISKY_BITS = ("pigeon_brain/", "node_memory", "registry", "copilot-instructions")
SOURCE_SUFFIXES = {".py", ".ps1", ".js", ".jsx", ".ts", ".tsx", ".css", ".html"}
DEFAULT_CONFIG = {
    "enabled": True,
    "fire_on": ["manual", "pre_prompt", "composition", "composition_submit", "log_prompt", "os_hook_auto"],
    "max_proposals": 6,
    "history_limit": 10000,
    "source_only": True,
    "target_state": "interlinked_source_state",
    "min_chars": 8,
    "min_interlink_score": 0.0,
    "auto_apply": False,
    "orchestrator_oath": True,
    "push_narrative_file_comedy": True,
    "orchestrator_policy": {
        "orchestrator_only": True,
        "monitor_per_prompt": True,
        "email_per_prompt": True,
        "approval_required": True,
        "auto_write_allowed": False,
    },
    "consensus_guard": {
        "enabled": True,
        "min_score": 7,
        "required_passes": [
            "intent_alignment",
            "context_available",
            "validation_plan",
            "source_target",
            "operator_approval",
        ],
        "email_send_policy": "block_resend_when_failed",
        "deepseek_queue_policy": "only_when_passed",
    },
    "rewrite_orchestration": {
        "proposal_model": "gemini_quick",
        "grader_model": "gemini_quick_grader",
        "context_injector": "manifest_prompt_brain_context_pack",
        "deep_rewrite_model": "deepseek_deep_path",
        "reasoning_policy": {
            "proposal": "low_latency",
            "grader": "focused",
            "overwrite": "deep_only_after_approval",
            "compile": "strict_validation",
        },
    },
    "compiler_layers": {
        "file_history": True,
        "distributed_intent_encoding": True,
        "self_monitoring": True,
        "file_identity_dynamic_growth": True,
        "file_self_learning": True,
    },
}


def simulate_batch_rewrites(
    root: Path,
    intent: str = "",
    limit: int | None = None,
    write: bool = True,
    config: dict[str, Any] | None = None,
    trigger: str = "manual",
    context_selection: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(root)
    config = merge_file_sim_config(config or load_file_sim_config(root, write_default=write))
    limit = int(limit or config.get("max_proposals") or 6)
    compiled = compile_intent(root, intent)
    history = _load_jsonl(root / "logs" / "dead_token_collective_pairs.jsonl", int(config.get("history_limit") or 10000))
    dead_summary = _load_json(root / "logs" / "dead_token_collective_history.json") or {}
    failure = _load_failure_model(root)
    dirty = _git_status(root)
    candidates = _rank_candidates(root, compiled, history, dead_summary, failure, dirty, limit, config, context_selection)
    _attach_incompatibility_reports(candidates)
    _attach_consensus_scores(candidates, compiled, config)
    now = _now()
    result = {
        "schema": SCHEMA,
        "status": "fired",
        "ts": now,
        "trigger": trigger,
        "root": str(root),
        "mode": "source_rewrite_orchestration",
        "target_state": config.get("target_state", "interlinked_source_state"),
        "write_policy": "source_rewrite_after_orchestrator_approval",
        "file_sim_config": config,
        "rewrite_orchestration": _rewrite_orchestration(config),
        "intent": compiled,
        "distributed_intent_encoding": _distributed_intent_encoding(context_selection, compiled),
        "self_model": {
            "history_pairs": len(history),
            "avg_fix_rate": failure.get("avg_fix_rate"),
            "persistent_modules": failure.get("persistent_modules", [])[:10],
            "dirty_files": sorted(dirty)[:20],
        },
        "orchestrator": {
            "orchestrator_only": bool((config.get("orchestrator_policy") or {}).get("orchestrator_only", True)),
            "monitor_per_prompt": bool((config.get("orchestrator_policy") or {}).get("monitor_per_prompt", True)),
            "email_per_prompt": bool((config.get("orchestrator_policy") or {}).get("email_per_prompt", True)),
            "approval_required": bool((config.get("orchestrator_policy") or {}).get("approval_required", True)),
            "auto_write_allowed": bool((config.get("orchestrator_policy") or {}).get("auto_write_allowed", False)),
            "overwrite_policy": "quick proposal -> grader -> context injection -> incompatibility report -> approval -> deepseek rewrite -> compile",
            "next_allowed_actions": [
                "inject_context_pack",
                "request_operator_approval",
                "run_dry_source_rewrite",
                "apply_source_rewrite_after_approval",
                "run_cross_file_validation",
            ],
        },
        "orchestrator_oath": _orchestrator_oath(compiled),
        "proposals": candidates,
        "paths": {
            "latest": "logs/batch_rewrite_sim_latest.json",
            "history": "logs/batch_rewrite_sim.jsonl",
            "narrative": "logs/batch_rewrite_sim.md",
            "fire_history": "logs/file_sim_fire_history.jsonl",
            "config": "logs/file_sim_config.json",
            "deepseek_code_completion_jobs": "logs/deepseek_code_completion_jobs.jsonl",
            "orchestrator_dev_oath": "logs/orchestrator_dev_oath.md",
            "file_push_narrative_fragment": "logs/file_push_narrative_fragment.md",
            "file_job_council": "logs/file_job_council_latest.json",
            "file_job_council_history": "logs/file_job_council.jsonl",
            "file_job_council_markdown": "logs/file_job_council.md",
            "file_self_sim_learning": "logs/file_self_sim_learning_latest.json",
            "deepseek_learning_packets": "logs/deepseek_learning_packets.jsonl",
        },
    }
    result["file_job_council"] = _file_job_council(root, result)
    if write:
        logs = root / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        for proposal in candidates:
            _append_jsonl(logs / "file_identity_growth.jsonl", _identity_growth_record(result, proposal))
        result["deepseek_code_completion"] = _queue_deepseek_completion_jobs(root, result)
        result["file_job_council"] = _file_job_council(root, result)
        _write_json(logs / "file_job_council_latest.json", result["file_job_council"])
        _append_jsonl(logs / "file_job_council.jsonl", result["file_job_council"])
        (logs / "file_job_council.md").write_text(_render_file_job_council(result["file_job_council"]), encoding="utf-8")
        if (config.get("compiler_layers") or {}).get("file_self_learning", True):
            try:
                from src.file_self_sim_learning_seq001_v001 import simulate_file_self_learning
                result["file_self_learning"] = simulate_file_self_learning(
                    root,
                    intent=compiled.get("raw", ""),
                    limit=limit,
                    write=True,
                    source_result=result,
                    config=config,
                )
            except Exception as exc:
                result["file_self_learning_error"] = str(exc)
        try:
            from src.file_email_plugin_seq001_v001 import emit_file_sim_emails
            result["file_email"] = emit_file_sim_emails(root, result)
        except Exception as exc:
            result["file_email_error"] = str(exc)
        (logs / "orchestrator_dev_oath.md").write_text(_render_orchestrator_oath(result), encoding="utf-8")
        fragment = _render_file_push_narrative_fragment(result)
        (logs / "file_push_narrative_fragment.md").write_text(fragment, encoding="utf-8")
        _append_jsonl(logs / "file_push_narrative_fragments.jsonl", {
            "schema": "file_push_narrative_fragment/v1",
            "ts": result.get("ts"),
            "intent_key": (result.get("intent") or {}).get("intent_key", ""),
            "fragment": fragment,
        })
        (logs / "batch_rewrite_sim.md").write_text(render_batch_rewrite_sim(result), encoding="utf-8")
        _write_json(logs / "batch_rewrite_sim_latest.json", result)
        _append_jsonl(logs / "batch_rewrite_sim.jsonl", result)
        _append_jsonl(logs / "file_sim_fire_history.jsonl", _fire_record(result))
    return result


def load_file_sim_config(root: Path, write_default: bool = True) -> dict[str, Any]:
    root = Path(root)
    path = root / "logs" / "file_sim_config.json"
    raw = _load_json(path) if path.exists() else {}
    config = merge_file_sim_config(raw if isinstance(raw, dict) else {})
    if write_default and (not path.exists() or raw != config):
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(path, config)
    return config


def merge_file_sim_config(config: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(DEFAULT_CONFIG))
    for key, value in (config or {}).items():
        if key in {"compiler_layers", "rewrite_orchestration", "consensus_guard", "orchestrator_policy"} and isinstance(value, dict):
            base = merged.get(key) if isinstance(merged.get(key), dict) else {}
            base.update(value)
            merged[key] = base
        elif key == "fire_on" and isinstance(value, list):
            merged[key] = list(dict.fromkeys([*DEFAULT_CONFIG["fire_on"], *value, "composition_submit", "os_hook_auto"]))
        else:
            merged[key] = value
    return merged


def should_fire_file_sim(config: dict[str, Any], trigger: str, prompt: str) -> bool:
    config = merge_file_sim_config(config)
    if not config.get("enabled", True):
        return False
    if trigger not in set(config.get("fire_on") or []):
        return False
    return len(str(prompt or "").strip()) >= int(config.get("min_chars") or 0)


def compile_intent(root: Path, intent: str = "") -> dict[str, Any]:
    root = Path(root)
    latest = _load_json(Path(root) / "logs" / "intent_key_latest.json") or {}
    raw = (intent or latest.get("prompt") or "").strip()
    words = _token_list(raw)
    tokens = set(words)
    verb = _choose_verb(tokens)
    scale = "major" if tokens & {"rewrite", "rewrites", "batch", "migrate", "migration"} else "patch"
    if intent:
        scope_info = _choose_scope_from_manifests(root, tokens)
        scope = scope_info.get("scope", "root")
        manifest_path = scope_info.get("manifest_path", "")
        confidence = scope_info.get("confidence", 0)
    else:
        scope = str(latest.get("scope") or "root")
        manifest_path = str(latest.get("manifest_path", ""))
        confidence = latest.get("confidence", 0)
    target = "_".join(words[:5])[:64] or str(latest.get("target") or "work")
    return {
        "raw": raw,
        "tokens": words[:40],
        "intent_key": f"{scope}:{verb}:{target}:{scale}",
        "scope": scope,
        "verb": verb,
        "target": target,
        "scale": scale,
        "manifest_path": manifest_path,
        "latest_confidence": confidence,
    }


def render_batch_rewrite_sim(result: dict[str, Any]) -> str:
    intent = result.get("intent", {})
    lines = [
        "# Batch Rewrite Sim",
        "",
        "Source rewrite orchestration lane. It compiles intent, proposes fixes, waits for approval,",
        "injects extra context, explains incompatible layouts, then reserves deep rewrite tokens for approved overwrites.",
        "",
        "```text",
        f"intent_key: {intent.get('intent_key', '')}",
        f"mode: {result.get('mode')}",
        f"target_state: {result.get('target_state')}",
        f"auto_write_allowed: {result.get('orchestrator', {}).get('auto_write_allowed')}",
        "```",
        "",
        "## Rewrite Ladder",
        "",
    ]
    ladder = result.get("rewrite_orchestration") or {}
    for stage in ladder.get("stages", []):
        lines.append(f"- `{stage.get('name')}` via `{stage.get('engine')}` - {stage.get('budget')}")
    lines.extend([
        "",
        "## Dead Token Collective Hearing",
        "",
        "The old filenames testify. Source files get rewritten toward interlinked state.",
        "",
    ])
    for i, prop in enumerate(result.get("proposals", [])[:10], 1):
        lines.extend([
            f"### Q{i} - {prop.get('path')}",
            "",
            f"- decision: `{prop.get('decision')}`",
            f"- reward: `{prop.get('reward')}` risk: `{prop.get('risk')}` confidence: `{prop.get('confidence')}`",
            f"- proposed_fix: {prop.get('proposed_fix')}",
            f"- approval_gate: `{prop.get('approval_gate')}`",
            f"- overwrite_path: `{prop.get('overwrite_path')}`",
            f"- context_injection: `{', '.join(prop.get('context_injection', [])[:5]) or 'none'}`",
            f"- validation: `{', '.join(prop.get('validation_plan', [])[:4]) or 'none'}`",
            f"- incompatibilities: `{_render_incompatibilities(prop)}`",
            f"- 10Q consensus: `{_render_ten_q(prop)}`",
            f"- email_guard: `{_render_email_guard(prop)}`",
            "",
        ])
    council = result.get("file_job_council") or {}
    if council:
        lines.extend([
            "## File Job Council",
            "",
            council.get("comedy_summary", "Files organized themselves into context packs."),
            "",
        ])
        for job in (council.get("jobs") or [])[:6]:
            lines.extend([
                f"### {job.get('job_id')} - {job.get('scope')}",
                "",
                f"- captain: `{job.get('captain')}`",
                f"- status: `{job.get('status')}`",
                f"- total_estimated_tokens: `{job.get('total_estimated_tokens')}`",
                f"- files: `{', '.join(job.get('files', [])[:6]) or 'none'}`",
                f"- why: {job.get('why')}",
                "",
            ])
        lines.extend(["### Context Packs", ""])
        for pack in (council.get("context_packs") or [])[:6]:
            lines.append(
                f"- `{pack.get('pack_id')}` {pack.get('purpose')} "
                f"({pack.get('total_estimated_tokens')}/{pack.get('token_budget')} tokens, "
                f"skipped {len(pack.get('skipped_files') or [])}): "
                f"`{', '.join(pack.get('files', [])[:8]) or 'none'}`"
            )
        lines.extend(["", "### Relationships", ""])
        for edge in (council.get("relationships") or [])[:8]:
            lines.append(
                f"- `{edge.get('from')}` {edge.get('type')} `{edge.get('to')}` - {edge.get('reason')}"
            )
        lines.append("")
    lines.extend([
        "## Final Rule",
        "",
        "The simulator can propose. File emails testify. DeepSeek drafts only after approval. Copilot executes and validates.",
        "",
        "## Orchestrator Oath",
        "",
        result.get("orchestrator_oath", {}).get("short", "No oath recorded."),
        "",
    ])
    return "\n".join(lines)


def _file_job_council(root: Path, result: dict[str, Any]) -> dict[str, Any]:
    proposals = [item for item in (result.get("proposals") or []) if isinstance(item, dict)]
    intent = result.get("intent") or {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    roster = []
    relationships = []
    for index, proposal in enumerate(proposals):
        member = _job_council_member(root, proposal, index)
        roster.append(member)
        grouped[member["scope"]].append(member)
        for friend in member.get("friendships", []):
            relationships.append({
                "from": member["file"],
                "to": friend,
                "type": "friendship",
                "reason": "shared context pack wants both files loaded",
            })
        for target in member.get("beefs", []):
            relationships.append({
                "from": member["file"],
                "to": target,
                "type": "beef",
                "reason": "compatibility report says rewrite order matters",
            })

    jobs = []
    for scope, members in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        captain = max(members, key=lambda item: (item.get("interlink_score", 0), item.get("confidence", 0)))
        failed = sum(int(item.get("failed_checks", 0)) for item in members)
        passed = sum(int(item.get("passed_checks", 0)) for item in members)
        files = _dedupe_strings([member["file"] for member in members])
        context_files = _dedupe_strings(
            [file_name for member in members for file_name in member.get("context_files", [])]
        )
        total_tokens = sum(int(member.get("approx_tokens") or 0) for member in members)
        job_id = "job-" + hashlib.sha256(
            f"{intent.get('intent_key', '')}|{scope}|{','.join(files)}".encode("utf-8")
        ).hexdigest()[:10]
        jobs.append({
            "job_id": job_id,
            "scope": scope,
            "goal": f"{intent.get('verb', 'route')} `{scope}` toward `{result.get('target_state', 'interlinked_source_state')}`",
            "captain": captain["file"],
            "files": files,
            "context_files": context_files,
            "total_estimated_tokens": total_tokens,
            "passed_checks": passed,
            "failed_checks": failed,
            "status": "ready_for_operator_approval" if failed == 0 else "needs_context_or_repair",
            "why": _job_why(scope, members, failed),
        })

    context_packs = _context_packs(root, proposals, roster, jobs)
    total_tokens = sum(int(member.get("approx_tokens") or 0) for member in roster)
    return {
        "schema": "file_job_council/v1",
        "ts": result.get("ts"),
        "intent_key": intent.get("intent_key", ""),
        "target_state": result.get("target_state", "interlinked_source_state"),
        "total_proposals": len(proposals),
        "total_estimated_tokens": total_tokens,
        "jobs": jobs,
        "context_packs": context_packs,
        "relationships": relationships[:80],
        "roster": roster[:40],
        "comedy_summary": _job_council_summary(jobs, relationships, roster),
    }


def _job_council_member(root: Path, proposal: dict[str, Any], index: int) -> dict[str, Any]:
    rel = str(proposal.get("path") or "unknown").replace("\\", "/")
    validation = proposal.get("cross_file_validation") or {}
    context_files = _dedupe_strings(str(item).replace("\\", "/") for item in (proposal.get("context_injection") or []))
    friendships = [
        item for item in context_files
        if item != rel and not item.lower().endswith("manifest.md")
    ]
    refs = [
        str(item).replace("\\", "/")
        for item in (validation.get("referenced_by") or [])
        if item and str(item).replace("\\", "/") != rel
    ]
    friendships = _dedupe_strings([*friendships, *refs])[:8]
    beefs = _dedupe_strings(
        str(item.get("with") or "").replace("\\", "/")
        for item in (proposal.get("incompatibilities") or [])
        if isinstance(item, dict) and item.get("with")
    )
    checks = (proposal.get("ten_q") or {}).get("checks") or []
    failed = [item for item in checks if isinstance(item, dict) and not item.get("passed")]
    passed = [item for item in checks if isinstance(item, dict) and item.get("passed")]
    return {
        "file": rel,
        "scope": Path(rel).parent.as_posix() or "root",
        "role": _job_role(index, rel, proposal, failed, friendships),
        "approx_tokens": _proposal_token_estimate(root, proposal),
        "interlink_score": proposal.get("interlink_score", 0),
        "confidence": proposal.get("confidence", 0),
        "decision": proposal.get("decision", ""),
        "context_files": context_files,
        "friendships": friendships,
        "beefs": beefs,
        "passed_checks": len(passed),
        "failed_checks": len(failed),
        "failed_check_keys": [str(item.get("key", "unknown")) for item in failed[:8]],
        "accumulated_sims": sum(int(value) for value in (proposal.get("event_counts") or {}).values()),
        "mood": _member_mood(rel, failed, friendships, beefs),
        "model_grievance": _model_grievance(proposal, failed),
    }


def _job_role(
    index: int,
    rel: str,
    proposal: dict[str, Any],
    failed: list[dict[str, Any]],
    friendships: list[str],
) -> str:
    if index == 0:
        return "captain"
    if failed:
        return "complainant"
    if Path(rel).name.startswith("test_") or any("pytest" in str(step) for step in proposal.get("validation_plan") or []):
        return "validator"
    if friendships:
        return "context_witness"
    return "worker"


def _member_mood(rel: str, failed: list[dict[str, Any]], friendships: list[str], beefs: list[str]) -> str:
    if failed:
        keys = ", ".join(str(item.get("key", "unknown")) for item in failed[:3])
        return f"{Path(rel).name} is loudly pointing at failed checks: {keys}"
    if beefs:
        return f"{Path(rel).name} will cooperate after {Path(beefs[0]).name} stops moving the furniture"
    if friendships:
        return f"{Path(rel).name} wants {Path(friendships[0]).name} loaded beside it before anyone gets clever"
    return f"{Path(rel).name} is calm, which the council considers suspicious"


def _model_grievance(proposal: dict[str, Any], failed: list[dict[str, Any]]) -> str:
    guard = proposal.get("orchestrator_email_guard") or {}
    ten_q = proposal.get("ten_q") or {}
    job_id = str(proposal.get("deepseek_completion_job_id") or "")
    if failed:
        return f"grader blocked the parade: {ten_q.get('reason', 'failed consensus')}"
    if job_id.startswith("blocked"):
        return f"deep path is sulking in `{job_id}` until consensus stops wobbling"
    if not job_id:
        return "deep path has not received a ticket yet"
    if guard.get("decision") != "allow_email":
        return f"email guard said `{guard.get('decision', 'unknown')}` and everyone is pretending that is normal"
    return "model stack behaved, which means validation should still check its pockets"


def _proposal_token_estimate(root: Path, proposal: dict[str, Any]) -> int:
    rel = str(proposal.get("path") or "")
    tokens = _estimate_file_tokens(root, rel)
    if tokens:
        return tokens
    lines = int((proposal.get("cross_file_validation") or {}).get("line_count") or 0)
    return max(1, lines * 8)


def _estimate_file_tokens(root: Path, rel: str) -> int:
    path = root / str(rel).replace("\\", "/")
    if not path.exists() or not path.is_file():
        return 0
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return 0
    return max(1, len(text) // 4)


def _dedupe_strings(values: Any) -> list[str]:
    seen = set()
    out = []
    for value in values or []:
        text = str(value or "").replace("\\", "/").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _context_packs(
    root: Path,
    proposals: list[dict[str, Any]],
    roster: list[dict[str, Any]],
    jobs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    primary = _dedupe_strings(
        [str(prop.get("path") or "") for prop in proposals[:4]]
        + [item for prop in proposals[:4] for item in (prop.get("context_injection") or [])]
    )
    validation = _dedupe_strings(
        item
        for prop in proposals
        for item in _validation_context_files(prop)
    )
    relationship = _dedupe_strings(
        item
        for member in roster
        for item in [*member.get("friendships", []), *member.get("beefs", [])]
    )
    job_files = _dedupe_strings(
        item
        for job in jobs
        for item in [*job.get("files", []), *job.get("context_files", [])]
    )
    packs = [
        _context_pack(root, "pack-primary", "load first for the code completion pass", primary[:12], 24000),
        _context_pack(root, "pack-validation", "load when compile/test gates are being judged", validation[:12], 16000),
        _context_pack(root, "pack-relationships", "load to explain friendships, conflicts, and import edges", relationship[:16], 24000),
        _context_pack(root, "pack-job-all", "bounded full job context for the current sim", job_files[:24], 48000),
    ]
    return [pack for pack in packs if pack.get("files")]


def _validation_context_files(proposal: dict[str, Any]) -> list[str]:
    out = []
    for step in proposal.get("validation_plan") or []:
        for match in re.findall(r"[A-Za-z0-9_./\\-]+\.(?:py|json|md|ts|tsx|js)", str(step)):
            out.append(match.replace("\\", "/"))
    return out


def _context_pack(root: Path, pack_id: str, purpose: str, files: list[str], token_budget: int) -> dict[str, Any]:
    selected = []
    skipped = []
    total = 0
    for file_name in _dedupe_strings(files):
        tokens = _estimate_file_tokens(root, file_name)
        if selected and total + tokens > token_budget:
            skipped.append({"file": file_name, "estimated_tokens": tokens, "reason": "context pack token budget"})
            continue
        selected.append(file_name)
        total += tokens
    return {
        "pack_id": pack_id,
        "purpose": purpose,
        "token_budget": token_budget,
        "files": selected,
        "total_estimated_tokens": total,
        "skipped_files": skipped[:20],
    }


def _job_why(scope: str, members: list[dict[str, Any]], failed: int) -> str:
    if failed:
        loud = max(members, key=lambda item: int(item.get("failed_checks") or 0))
        return f"`{scope}` needs repair/context because `{loud.get('file')}` failed {loud.get('failed_checks')} checks"
    captain = max(members, key=lambda item: (item.get("interlink_score", 0), item.get("confidence", 0)))
    return f"`{scope}` is coherent enough for approval; `{captain.get('file')}` is carrying the intent"


def _job_council_summary(
    jobs: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    roster: list[dict[str, Any]],
) -> str:
    failures = sum(int(member.get("failed_checks") or 0) for member in roster)
    beefs = sum(1 for edge in relationships if edge.get("type") == "beef")
    friends = sum(1 for edge in relationships if edge.get("type") == "friendship")
    tokens = sum(int(member.get("approx_tokens") or 0) for member in roster)
    job_word = "job" if len(jobs) == 1 else "jobs"
    if failures:
        return (
            f"{len(jobs)} {job_word} formed around {tokens} estimated tokens. "
            f"{friends} friendships tried to help, {beefs} beefs filed paperwork, "
            f"and {failures} failed checks are yelling at the broken model stack."
        )
    return (
        f"{len(jobs)} {job_word} formed around {tokens} estimated tokens. "
        f"{friends} friendships loaded context, {beefs} beefs stayed documented, "
        "and the files are suspiciously ready for approval."
    )


def _render_file_job_council(council: dict[str, Any]) -> str:
    lines = [
        "# File Job Council",
        "",
        f"- intent_key: `{council.get('intent_key', '')}`",
        f"- total_estimated_tokens: `{council.get('total_estimated_tokens', 0)}`",
        f"- total_proposals: `{council.get('total_proposals', 0)}`",
        "",
        council.get("comedy_summary", ""),
        "",
        "## Jobs",
        "",
    ]
    for job in council.get("jobs", []):
        lines.extend([
            f"### {job.get('job_id')} - {job.get('scope')}",
            "",
            f"- status: `{job.get('status')}`",
            f"- captain: `{job.get('captain')}`",
            f"- tokens: `{job.get('total_estimated_tokens')}`",
            f"- files: `{', '.join(job.get('files', []))}`",
            f"- context_files: `{', '.join(job.get('context_files', [])[:12])}`",
            f"- why: {job.get('why')}",
            "",
        ])
    lines.extend(["## Context Packs", ""])
    for pack in council.get("context_packs", []):
        lines.append(
            f"- `{pack.get('pack_id')}` ({pack.get('total_estimated_tokens')}/{pack.get('token_budget')} tokens, "
            f"skipped {len(pack.get('skipped_files') or [])}): "
            f"{', '.join(pack.get('files', []))}"
        )
    lines.extend(["", "## Roster", ""])
    for member in council.get("roster", [])[:20]:
        lines.append(
            f"- `{member.get('file')}` as `{member.get('role')}` "
            f"({member.get('approx_tokens')} tokens): {member.get('mood')} "
            f"Model grievance: {member.get('model_grievance')}"
        )
    lines.extend(["", "## Relationships", ""])
    for edge in council.get("relationships", [])[:40]:
        lines.append(f"- `{edge.get('from')}` {edge.get('type')} `{edge.get('to')}` - {edge.get('reason')}")
    lines.append("")
    return "\n".join(lines)


def _rank_candidates(
    root: Path,
    compiled: dict[str, Any],
    history: list[dict[str, Any]],
    dead_summary: dict[str, Any],
    failure: dict[str, Any],
    dirty: set[str],
    limit: int,
    config: dict[str, Any],
    context_selection: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    bucket: dict[str, dict[str, Any]] = defaultdict(lambda: {"score": 0.0, "events": Counter(), "evidence": []})
    tokens = set(compiled.get("tokens") or [])
    scope = str(compiled.get("scope") or "")

    for path, points, reason in _seed_paths(root, compiled, dead_summary, context_selection):
        _add_candidate(bucket, path, points, reason)
    for pair in history:
        path = pair.get("new_path") or pair.get("old_path") or ""
        points = _history_points(pair, tokens, scope)
        if path and points > 0:
            row = bucket[path]
            row["score"] += points
            row["events"][str(pair.get("event_type") or "touch")] += 1
            if len(row["evidence"]) < 5:
                row["evidence"].append(str(pair.get("subject") or pair.get("prompt") or "")[:140])
    if not bucket:
        for path, points, reason in _fallback_prompt_sim_targets(root):
            _add_candidate(bucket, path, points, reason)

    ranked_all = sorted(
        bucket.items(),
        key=lambda kv: _candidate_sort_score(root, kv[0], kv[1], set(compiled.get("tokens") or [])),
        reverse=True,
    )
    ranked_source = [(p, d) for p, d in ranked_all if _source_candidate(p)]
    ranked_other = [(p, d) for p, d in ranked_all if not _source_candidate(p)]
    ranked = ranked_source + ranked_other
    proposals = []
    source_only = bool(config.get("source_only", True))
    min_interlink = float(config.get("min_interlink_score") or 0)
    for path, data in ranked[: max(limit * 3, limit)]:
        proposal = _proposal(root, path, data, compiled, failure, dirty, config)
        if source_only and proposal["rewrite_target_type"] != "source":
            continue
        if proposal["interlink_score"] < min_interlink:
            continue
        proposals.append(proposal)
        if len(proposals) >= limit:
            break
    return proposals


def _fallback_prompt_sim_targets(root: Path) -> list[tuple[str, float, str]]:
    candidates = [
        "codex_compat.py",
        "src/batch_rewrite_sim_seq001_v001.py",
        "src/file_self_sim_learning_seq001_v001.py",
        "src/file_email_plugin_seq001_v001.py",
        "src/intent_loop_closer_seq001_v001.py",
    ]
    return [
        (rel, 0.7, "prompt_contract_fallback_core_file")
        for rel in candidates
        if (root / rel).exists()
    ]


def _proposal(
    root: Path,
    rel: str,
    data: dict[str, Any],
    compiled: dict[str, Any],
    failure: dict[str, Any],
    dirty: set[str],
    config: dict[str, Any],
) -> dict[str, Any]:
    path = root / rel
    validation = _cross_file_validation(root, rel, dirty)
    stem = _stem_key(rel)
    chronic = stem in set(failure.get("persistent_modules", []))
    risky_path = rel.replace("\\", "/")
    risk = 0.12
    risk += 0.22 if _metadata_candidate(rel, set(compiled.get("tokens") or [])) else 0
    risk += 0.34 if not _source_candidate(rel) else 0
    risk += 0.28 if not path.exists() else 0
    risk += 0.18 if rel in dirty else 0
    risk += 0.18 if path.suffix.lower() in RISKY_SUFFIXES else 0
    risk += 0.18 if any(bit in risky_path for bit in RISKY_BITS) else 0
    risk += 0.14 if validation.get("line_count", 0) > 400 else 0
    risk += 0.12 if chronic else 0
    interlink = _interlink_score(rel, validation, compiled)
    reward = min(1.0, 0.18 + data["score"] / 6 + min(sum(data["events"].values()), 20) / 40 + interlink * 0.22)
    confidence = max(0.0, min(1.0, reward * (1.0 - min(risk, 0.95))))
    decision = "safe_dry_run" if confidence >= 0.35 and risk < 0.45 else "needs_review"
    if risk >= 0.72 or not path.exists():
        decision = "blocked"
    return {
        "path": rel,
        "rewrite_target_type": "source" if _source_candidate(rel) else "context_memory",
        "target_state": config.get("target_state", "interlinked_source_state"),
        "interlink_score": round(interlink, 3),
        "decision": decision,
        "approval_gate": "operator_required",
        "overwrite_path": _overwrite_path(decision, rel),
        "reasoning_budget": _reasoning_budget(decision),
        "reward": round(reward, 3),
        "risk": round(min(risk, 1.0), 3),
        "confidence": round(confidence, 3),
        "event_counts": dict(data["events"]),
        "evidence": data["evidence"][:5],
        "failure_memory": {"chronic_or_eternal": chronic},
        "identity_growth": _identity_growth(compiled, rel, validation, interlink),
        "proposed_fix": _proposed_fix(compiled, rel, decision),
        "context_injection": _context_injection(compiled, rel, validation),
        "validation_plan": _validation_plan(rel, validation),
        "incompatibilities": [],
        "cross_file_validation": validation,
    }


def _rewrite_orchestration(config: dict[str, Any]) -> dict[str, Any]:
    orch = config.get("rewrite_orchestration") if isinstance(config.get("rewrite_orchestration"), dict) else {}
    policy = orch.get("reasoning_policy") if isinstance(orch.get("reasoning_policy"), dict) else {}
    return {
        "principle": "do not spend deep rewrite tokens until a candidate survives proposal, grading, context injection, compatibility, and approval",
        "stages": [
            {
                "name": "proposal",
                "engine": orch.get("proposal_model", "gemini_quick"),
                "budget": policy.get("proposal", "low_latency"),
                "purpose": "cheap candidate generation from intent, history, and file identity",
            },
            {
                "name": "grader",
                "engine": orch.get("grader_model", "gemini_quick_grader"),
                "budget": policy.get("grader", "focused"),
                "purpose": "reject vague, stale, or low-interlink proposals",
            },
            {
                "name": "context_injection",
                "engine": orch.get("context_injector", "manifest_prompt_brain_context_pack"),
                "budget": "deterministic",
                "purpose": "assemble manifests, prompt brain, peer files, and validation plan",
            },
            {
                "name": "compatibility_referee",
                "engine": "local_cross_file_layout_check",
                "budget": "deterministic",
                "purpose": "tell files why competing proposals cannot both land",
            },
            {
                "name": "deep_rewrite_compile",
                "engine": orch.get("deep_rewrite_model", "deepseek_deep_path"),
                "budget": policy.get("overwrite", "deep_only_after_approval"),
                "purpose": "approved source overwrite followed by compile/test validation",
            },
        ],
    }


def _overwrite_path(decision: str, rel: str) -> str:
    if decision == "blocked":
        return "blocked_before_overwrite"
    if not _source_candidate(rel):
        return "context_only_no_overwrite"
    return "eligible_for_deepseek_after_approval"


def _reasoning_budget(decision: str) -> dict[str, str]:
    if decision == "blocked":
        return {"proposal": "quick", "grader": "quick", "deep_rewrite": "none"}
    return {"proposal": "quick", "grader": "focused", "deep_rewrite": "full_after_approval"}


def _attach_incompatibility_reports(proposals: list[dict[str, Any]]) -> None:
    for proposal in proposals:
        reports = []
        path = str(proposal.get("path") or "")
        edges = _context_edges(proposal)
        for other in proposals:
            other_path = str(other.get("path") or "")
            if not other_path or other_path == path:
                continue
            other_edges = _context_edges(other)
            shared = sorted((edges & other_edges) - {path, other_path})
            if shared:
                reports.append({
                    "with": other_path,
                    "severity": "medium",
                    "reason": f"shared context edge {shared[0]} means rewrite order or merged context is required",
                })
            if Path(path).name == "__init__.py" and str(other_path).startswith(str(Path(path).parent).replace("\\", "/")):
                reports.append({
                    "with": other_path,
                    "severity": "high",
                    "reason": "__init__ export layout can invalidate sibling rewrite assumptions",
                })
            if (proposal.get("cross_file_validation") or {}).get("dirty") and other_path in edges:
                reports.append({
                    "with": other_path,
                    "severity": "high",
                    "reason": "dirty working tree state must settle before peer rewrite is trusted",
                })
            if len(reports) >= 4:
                break
        proposal["incompatibilities"] = _dedupe_incompatibilities(reports)


def _attach_consensus_scores(
    proposals: list[dict[str, Any]],
    compiled: dict[str, Any],
    config: dict[str, Any],
) -> None:
    guard = config.get("consensus_guard") if isinstance(config.get("consensus_guard"), dict) else {}
    enabled = bool(guard.get("enabled", True))
    for proposal in proposals:
        ten_q = _compute_ten_q(proposal, compiled, guard)
        if not enabled:
            ten_q["passed"] = True
            ten_q["reason"] = "consensus_guard_disabled"
        proposal["ten_q"] = ten_q
        proposal["orchestrator_email_guard"] = _orchestrator_email_guard(proposal, ten_q, guard)


def _compute_ten_q(
    proposal: dict[str, Any],
    compiled: dict[str, Any],
    guard: dict[str, Any],
) -> dict[str, Any]:
    checks = _ten_q_checks(proposal, compiled)
    score = sum(1 for check in checks if check.get("passed"))
    by_key = {str(check.get("key")): bool(check.get("passed")) for check in checks}
    required = [str(item) for item in (guard.get("required_passes") or []) if item]
    min_score = int(guard.get("min_score") or 7)
    missing = [key for key in required if not by_key.get(key)]
    passed = score >= min_score and not missing
    return {
        "schema": "file_consensus_10q/v1",
        "score": score,
        "max_score": len(checks),
        "min_score": min_score,
        "passed": passed,
        "required_passes": required,
        "missing_required": missing,
        "checks": checks,
        "reason": "passed" if passed else _ten_q_failure_reason(score, min_score, missing),
    }


def _ten_q_checks(proposal: dict[str, Any], compiled: dict[str, Any]) -> list[dict[str, Any]]:
    validation = proposal.get("cross_file_validation") or {}
    identity = proposal.get("identity_growth") or {}
    context = proposal.get("context_injection") or []
    validation_plan = proposal.get("validation_plan") or []
    prompt_tokens = set(compiled.get("tokens") or [])
    file_tokens = _tokens(" ".join([
        str(proposal.get("path") or ""),
        str(proposal.get("proposed_fix") or ""),
        " ".join(str(item) for item in proposal.get("evidence") or []),
    ]))
    return [
        _check(
            "intent_alignment",
            bool(prompt_tokens and (prompt_tokens & file_tokens)) or bool(proposal.get("evidence")),
            "prompt/file/history tokens intersect",
            "no prompt or history signal explains this file",
        ),
        _check(
            "source_target",
            proposal.get("rewrite_target_type") == "source",
            "target is source code",
            "target is context or metadata only",
        ),
        _check(
            "context_available",
            bool(context),
            "context pack is present",
            "no context files selected",
        ),
        _check(
            "validation_plan",
            bool(validation_plan) and not str(validation_plan[0]).startswith("hold:"),
            "compile/test gate exists",
            "validation is missing or only hold",
        ),
        _check(
            "operator_approval",
            proposal.get("approval_gate") == "operator_required",
            "operator approval is required",
            "no operator approval gate",
        ),
        _check(
            "deepseek_job_allowed",
            proposal.get("overwrite_path") == "eligible_for_deepseek_after_approval",
            "deep rewrite path is eligible after approval",
            "deep rewrite path is blocked",
        ),
        _check(
            "incompatibility_known",
            isinstance(proposal.get("incompatibilities"), list),
            "peer incompatibility scan ran",
            "peer incompatibility scan missing",
        ),
        _check(
            "identity_growth",
            bool(identity) and float(identity.get("interlink_score") or 0) >= 0,
            "file identity growth record exists",
            "file identity growth was not computed",
        ),
        _check(
            "dirty_state_known",
            "dirty" in validation,
            "working tree state is known",
            "dirty state unknown",
        ),
        _check(
            "file_exists",
            bool(validation.get("exists")),
            "target file exists",
            "target file missing",
        ),
    ]


def _check(key: str, passed: bool, pass_reason: str, fail_reason: str) -> dict[str, Any]:
    return {"key": key, "passed": bool(passed), "reason": pass_reason if passed else fail_reason}


def _ten_q_failure_reason(score: int, min_score: int, missing: list[str]) -> str:
    parts = []
    if score < min_score:
        parts.append(f"score {score}/{min_score}")
    if missing:
        parts.append("missing required " + ", ".join(missing))
    return "; ".join(parts) or "failed consensus"


def _orchestrator_email_guard(
    proposal: dict[str, Any],
    ten_q: dict[str, Any],
    guard: dict[str, Any],
) -> dict[str, Any]:
    aligned = bool(ten_q.get("passed"))
    decision = "allow_email" if aligned else "local_only"
    if str(guard.get("email_send_policy") or "") == "block_all_when_failed" and not aligned:
        decision = "block_email"
    return {
        "schema": "orchestrator_email_guard/v1",
        "aligned": aligned,
        "decision": decision,
        "policy": guard.get("email_send_policy", "block_resend_when_failed"),
        "reason": "10Q consensus passed" if aligned else f"10Q consensus failed: {ten_q.get('reason')}",
    }


def _context_edges(proposal: dict[str, Any]) -> set[str]:
    edges = {str(proposal.get("path") or "")}
    edges.update(str(item) for item in (proposal.get("context_injection") or []) if item)
    validation = proposal.get("cross_file_validation") or {}
    edges.update(str(item) for item in (validation.get("referenced_by") or []) if item)
    return {edge.replace("\\", "/") for edge in edges if edge and not edge.lower().endswith("manifest.md")}


def _dedupe_incompatibilities(reports: list[dict[str, str]]) -> list[dict[str, str]]:
    seen = set()
    out = []
    for report in reports:
        key = (report.get("with"), report.get("reason"))
        if key in seen:
            continue
        seen.add(key)
        out.append(report)
    return out[:4]


def _render_incompatibilities(proposal: dict[str, Any]) -> str:
    reports = proposal.get("incompatibilities") or []
    if not reports:
        return "none"
    return "; ".join(
        f"{item.get('severity')} with {item.get('with')}: {item.get('reason')}"
        for item in reports[:3]
    )


def _render_ten_q(proposal: dict[str, Any]) -> str:
    ten_q = proposal.get("ten_q") or {}
    status = "PASS" if ten_q.get("passed") else "FAIL"
    return f"{status} {ten_q.get('score', 0)}/{ten_q.get('max_score', 10)} - {ten_q.get('reason', '')}"


def _render_email_guard(proposal: dict[str, Any]) -> str:
    guard = proposal.get("orchestrator_email_guard") or {}
    return f"{guard.get('decision', 'unknown')} - {guard.get('reason', '')}"


def _queue_deepseek_completion_jobs(root: Path, result: dict[str, Any]) -> dict[str, Any]:
    logs = root / "logs"
    jobs = []
    existing = {row.get("job_id") for row in _load_jsonl(logs / "deepseek_code_completion_jobs.jsonl", 200)}
    for proposal in result.get("proposals") or []:
        if proposal.get("overwrite_path") != "eligible_for_deepseek_after_approval":
            continue
        if not ((proposal.get("ten_q") or {}).get("passed") and (proposal.get("orchestrator_email_guard") or {}).get("aligned")):
            proposal["deepseek_completion_job_id"] = "blocked_by_consensus"
            continue
        job = _deepseek_completion_job(result, proposal)
        proposal["deepseek_completion_job_id"] = job["job_id"]
        if job["job_id"] in existing:
            job["duplicate"] = True
            jobs.append(job)
            continue
        _append_jsonl(logs / "deepseek_code_completion_jobs.jsonl", job)
        existing.add(job["job_id"])
        jobs.append(job)
    if jobs:
        _write_json(logs / "deepseek_code_completion_latest.json", jobs[-1])
    return {
        "status": "queued",
        "count": len(jobs),
        "model": _deepseek_model(),
        "jobs": [{"job_id": job["job_id"], "file": job["file"], "status": job["status"]} for job in jobs[:6]],
    }


def _deepseek_completion_job(result: dict[str, Any], proposal: dict[str, Any]) -> dict[str, Any]:
    file_path = str(proposal.get("path") or "unknown")
    intent = result.get("intent") or {}
    seed = json.dumps({
        "ts": result.get("ts"),
        "intent_key": intent.get("intent_key"),
        "file": file_path,
        "reason": proposal.get("proposed_fix"),
    }, sort_keys=True, ensure_ascii=False)
    job_id = "dsc-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]
    return {
        "schema": "deepseek_code_completion/v1",
        "ts": result.get("ts"),
        "job_id": job_id,
        "status": "queued_for_orchestrator_approval",
        "model": _deepseek_model(),
        "mode": "source_rewrite_completion",
        "file": file_path,
        "intent_key": intent.get("intent_key", ""),
        "target_state": result.get("target_state", "interlinked_source_state"),
        "reasoning_budget": (proposal.get("reasoning_budget") or {}).get("deep_rewrite", "full_after_approval"),
        "copilot_role": "sim_executor",
        "prompt": _deepseek_completion_prompt(result, proposal),
        "context_injection": proposal.get("context_injection", []),
        "validation_plan": proposal.get("validation_plan", []),
        "incompatibilities": proposal.get("incompatibilities", []),
        "ten_q": proposal.get("ten_q", {}),
        "orchestrator_email_guard": proposal.get("orchestrator_email_guard", {}),
        "approval_gate": proposal.get("approval_gate", "operator_required"),
        "autonomous_write": False,
    }


def _deepseek_completion_prompt(result: dict[str, Any], proposal: dict[str, Any]) -> str:
    intent = result.get("intent") or {}
    incompat = _render_incompatibilities(proposal)
    return "\n".join([
        "You are the DeepSeek deep source rewrite path.",
        "Draft a source rewrite plan or patch only for the approved file.",
        f"INTENT_KEY: {intent.get('intent_key', '')}",
        f"TARGET_STATE: {result.get('target_state', 'interlinked_source_state')}",
        f"FILE: {proposal.get('path')}",
        f"PROPOSED_FIX: {proposal.get('proposed_fix')}",
        f"INCOMPATIBILITIES: {incompat}",
        "CONTEXT_FILES:",
        *[f"- {item}" for item in (proposal.get("context_injection") or [])[:10]],
        "VALIDATION:",
        *[f"- {item}" for item in (proposal.get("validation_plan") or [])[:8]],
        "RULE: Do not overwrite until orchestrator approval exists. Copilot executes; validation can veto.",
    ])


def _deepseek_model() -> str:
    return os.environ.get("DEEPSEEK_CODING_MODEL") or os.environ.get("DEEPSEEK_MODEL") or "deepseek-v4-pro"


def _orchestrator_oath(compiled: dict[str, Any]) -> dict[str, Any]:
    intent_key = compiled.get("intent_key", "")
    lines = [
        "I will compile intent before action.",
        "I will let files testify before they are overwritten.",
        "I will use quick proposal and grading before spending deep rewrite tokens.",
        "I will inject context before execution.",
        "I will explain incompatible file proposals instead of hiding conflicts.",
        "I will let Copilot execute only bounded approved work.",
        "I will let validation veto every rewrite.",
    ]
    return {
        "schema": "orchestrator_dev_oath/v1",
        "intent_key": intent_key,
        "short": "Orchestrator oath: compile intent, hear file testimony, approve narrowly, execute with Copilot, validate before trust.",
        "lines": lines,
    }


def _render_orchestrator_oath(result: dict[str, Any]) -> str:
    oath = result.get("orchestrator_oath") or {}
    lines = [
        "# Orchestrator Dev Oath",
        "",
        f"- ts: `{result.get('ts')}`",
        f"- intent_key: `{(result.get('intent') or {}).get('intent_key', '')}`",
        "",
    ]
    for line in oath.get("lines", []):
        lines.append(f"- {line}")
    lines.extend([
        "",
        "Comic clause: files may have beef, but validation has the gavel.",
        "",
    ])
    return "\n".join(lines)


def _render_file_push_narrative_fragment(result: dict[str, Any]) -> str:
    council = result.get("file_job_council") or {}
    lines = [
        "## File Comedy Dispatch",
        "",
        f"Intent `{(result.get('intent') or {}).get('intent_key', '')}` ran the file-sim court.",
        "Files wrote local mail, filed beef, and queued DeepSeek completion jobs for approved source rewrite paths.",
        "",
    ]
    if council:
        lines.extend([
            f"Council summary: {council.get('comedy_summary', '')}",
            "",
        ])
        for job in (council.get("jobs") or [])[:4]:
            lines.append(
                f"- `{job.get('job_id')}` packs `{job.get('total_estimated_tokens')}` tokens "
                f"around captain `{job.get('captain')}`; status `{job.get('status')}`"
            )
        lines.append("")
    for proposal in (result.get("proposals") or [])[:6]:
        lines.append(
            f"- `{proposal.get('path')}` wants `{proposal.get('overwrite_path')}` "
            f"after `{proposal.get('approval_gate')}`; 10Q {_render_ten_q(proposal)}; "
            f"guard {_render_email_guard(proposal)}; beef/conflicts: {_render_incompatibilities(proposal)}"
        )
    lines.extend([
        "",
        "Oath: Copilot executes the approved sim. DeepSeek drafts the deep path. Validation gets the veto.",
        "",
    ])
    return "\n".join(lines)


def _seed_paths(
    root: Path,
    compiled: dict[str, Any],
    dead_summary: dict[str, Any],
    context_selection: dict[str, Any] | None,
) -> list[tuple[str, float, str]]:
    seeds: list[tuple[str, float, str]] = []
    tokens = set(compiled.get("tokens") or [])
    manifest = str(compiled.get("manifest_path") or "")
    if manifest:
        seeds.append((manifest, 0.3, "latest_intent_manifest_context"))
        scope_dir = root / Path(manifest).parent
        if scope_dir.exists():
            for path in sorted(scope_dir.glob("*.py"))[:10]:
                seeds.append((path.relative_to(root).as_posix(), 0.9, "manifest_scope_file"))
    ctx = context_selection if isinstance(context_selection, dict) else (_load_json(root / "logs" / "context_selection.json") or {})
    for item in ctx.get("files", [])[:8]:
        resolved = _resolve_stem(root, str(item.get("name", "")))
        if resolved:
            seeds.append((resolved, 1.2, "numeric_context_selection"))
    for item in (dead_summary.get("top_churn_files") or [])[:8]:
        churn_path = str(item.get("path", ""))
        seeds.append((churn_path, 0.35 if _source_candidate(churn_path) else 0.08, "top_churn_memory"))
    for path in sorted(root.glob("src/**/*.py"))[:2500]:
        rel = path.relative_to(root).as_posix()
        hits = len(tokens & _tokens(rel))
        if hits:
            seeds.append((rel, min(1.2, 0.2 + hits * 0.18), "intent_token_file_match"))
    return seeds


def _add_candidate(bucket: dict[str, dict[str, Any]], path: str, points: float, reason: str) -> None:
    if not path:
        return
    row = bucket[path.replace("\\", "/")]
    row["score"] += points
    if reason not in row["evidence"]:
        row["evidence"].append(reason)


def _history_points(pair: dict[str, Any], tokens: set[str], scope: str) -> float:
    path = str(pair.get("new_path") or pair.get("old_path") or "").replace("\\", "/")
    text = " ".join([path, str(pair.get("intent_key", "")), str(pair.get("subject", ""))])
    hits = len(tokens & _tokens(text))
    points = hits / max(len(tokens), 4)
    if scope and scope != "root" and "/" in scope and path.startswith(scope):
        points += 0.7
    if pair.get("event_type") in {"patch", "rename"}:
        points += 0.08
    return points if points >= 0.18 else 0.0


def _candidate_sort_score(root: Path, path: str, data: dict[str, Any], tokens: set[str]) -> float:
    score = float(data["score"])
    if _source_candidate(path):
        score += 1.4
    else:
        score -= 4.0
    if _metadata_candidate(path, tokens):
        score -= 1.8
    if not (root / path).exists():
        score -= 6.0
    return score


def _metadata_candidate(path: str, tokens: set[str]) -> bool:
    lower = path.lower().replace("\\", "/")
    if tokens & {"manifest", "manifests", "docs", "document", "documentation"}:
        return False
    return lower.endswith("/manifest.md") or lower.endswith("manifest.md")


def _source_candidate(path: str) -> bool:
    return Path(path).suffix.lower() in SOURCE_SUFFIXES


def _cross_file_validation(root: Path, rel: str, dirty: set[str]) -> dict[str, Any]:
    path = root / rel
    out = {"exists": path.exists(), "dirty": rel in dirty, "line_count": 0, "imports": [], "referenced_by": []}
    if not path.exists() or not path.is_file():
        return out
    text = path.read_text(encoding="utf-8", errors="ignore")
    out["line_count"] = len(text.splitlines())
    out["imports"] = [ln.strip() for ln in text.splitlines() if ln.lstrip().startswith(("import ", "from "))][:12]
    out["referenced_by"] = _referenced_by(root, path.stem, rel)[:8]
    return out


def _validation_plan(rel: str, validation: dict[str, Any]) -> list[str]:
    path = rel.replace("\\", "/")
    if not validation.get("exists"):
        return ["hold: target missing"]
    if path.endswith(".py"):
        stem = Path(path).stem
        return [f"py -m py_compile {path}", f"py -m pytest test_{stem}.py", "git diff --check"]
    if path.endswith(".json"):
        return [f"py -m json.tool {path}", "git diff --check"]
    return ["git diff --check", "manual context review"]


def _context_injection(compiled: dict[str, Any], rel: str, validation: dict[str, Any]) -> list[str]:
    files = [rel]
    manifest = compiled.get("manifest_path")
    if manifest:
        files.append(str(manifest))
    files.extend(validation.get("referenced_by", [])[:4])
    return list(dict.fromkeys(files))


def _proposed_fix(compiled: dict[str, Any], rel: str, decision: str) -> str:
    verb = compiled.get("verb")
    if decision == "blocked":
        return "hold; request operator context before rewrite"
    if _source_candidate(rel):
        return f"source rewrite {rel} toward interlinked state: intent hooks, context edges, validation surfaces"
    if verb == "refactor":
        return f"dry-run structural rewrite plan for {rel}; no source write"
    if verb == "validate":
        return f"compile and cross-file validate {rel} before patch proposal"
    return f"minimal targeted patch proposal for {rel}"


def _distributed_intent_encoding(context_selection: dict[str, Any] | None, compiled: dict[str, Any]) -> dict[str, Any]:
    context_selection = context_selection if isinstance(context_selection, dict) else {}
    files = []
    for item in (context_selection.get("files") or [])[:12]:
        if isinstance(item, dict):
            files.append({"name": item.get("name"), "score": item.get("score", 0)})
    return {
        "intent_key": compiled.get("intent_key", ""),
        "context_confidence": context_selection.get("confidence", 0),
        "context_status": context_selection.get("status", "unknown"),
        "file_votes": files,
        "stale_blocks": context_selection.get("stale_blocks", []),
    }


def _identity_growth(compiled: dict[str, Any], rel: str, validation: dict[str, Any], interlink: float) -> dict[str, Any]:
    stem = Path(rel).stem
    tokens = sorted((_tokens(rel) | set(compiled.get("tokens") or [])))[:16]
    return {
        "file": rel,
        "stem": stem,
        "identity_key": f"{_stem_key(stem)}:{compiled.get('verb', 'route')}:{compiled.get('target', 'work')}",
        "growth_tags": tokens,
        "interlink_score": round(interlink, 3),
        "imports_seen": len(validation.get("imports") or []),
        "referenced_by_seen": len(validation.get("referenced_by") or []),
    }


def _fire_record(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "file_sim_fire/v1",
        "ts": result.get("ts"),
        "trigger": result.get("trigger"),
        "status": result.get("status"),
        "intent_key": (result.get("intent") or {}).get("intent_key", ""),
        "target_state": result.get("target_state"),
        "proposal_count": len(result.get("proposals") or []),
        "top_files": [p.get("path") for p in (result.get("proposals") or [])[:5]],
    }


def _identity_growth_record(result: dict[str, Any], proposal: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "file_identity_growth/v1",
        "ts": result.get("ts"),
        "trigger": result.get("trigger"),
        "intent_key": (result.get("intent") or {}).get("intent_key", ""),
        **(proposal.get("identity_growth") or {}),
    }


def _interlink_score(rel: str, validation: dict[str, Any], compiled: dict[str, Any]) -> float:
    score = 0.0
    if _source_candidate(rel):
        score += 0.25
    refs = validation.get("referenced_by") or []
    imports = validation.get("imports") or []
    score += min(len(refs), 8) * 0.045
    score += min(len(imports), 10) * 0.02
    tokens = set(compiled.get("tokens") or [])
    path_tokens = _tokens(rel)
    score += min(len(tokens & path_tokens), 6) * 0.055
    if validation.get("line_count", 0) > 400:
        score -= 0.08
    return max(0.0, min(1.0, score))


def _load_failure_model(root: Path) -> dict[str, Any]:
    data = _load_json(root / "logs" / "self_fix_accuracy.json")
    if not isinstance(data, dict):
        data = {}
    persistent = []
    for row in data.get("persistent_top_10", []) or []:
        mod = str(row.get("module") or "").strip()
        if mod:
            persistent.append(_stem_key(mod))
    return {"avg_fix_rate": data.get("avg_fix_rate"), "persistent_modules": persistent}


def _git_status(root: Path) -> set[str]:
    result = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=False)
    dirty = set()
    for line in result.stdout.splitlines():
        if len(line) >= 4:
            dirty.add(line[3:].replace("\\", "/"))
    return dirty


def _referenced_by(root: Path, stem: str, self_rel: str) -> list[str]:
    result = subprocess.run(
        ["git", "-c", "core.quotePath=false", "grep", "-l", stem, "--", "*.py"],
        cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
    )
    out = []
    for line in result.stdout.splitlines():
        rel = _clean_rel_path(line)
        if rel and rel != self_rel and (root / rel).exists():
            out.append(rel)
    return out[:20]


def _clean_rel_path(value: str) -> str:
    text = value.strip().strip('"').replace("\\", "/")
    return text if text and ".." not in Path(text).parts else ""


def _resolve_stem(root: Path, name: str) -> str:
    if not name:
        return ""
    target = _stem_key(name)
    for path in sorted(root.glob("src/**/*.py"))[:2000]:
        if _stem_key(path.stem) == target or path.stem.startswith(name):
            return path.relative_to(root).as_posix()
    return ""


def _choose_verb(tokens: set[str]) -> str:
    best = ("route", 0)
    for verb, words in VERBS.items():
        hits = len(tokens & words)
        if hits > best[1]:
            best = (verb, hits)
    return best[0]


def _choose_scope_from_manifests(root: Path, tokens: set[str]) -> dict[str, Any]:
    best = {"scope": "root", "manifest_path": "", "confidence": 0.0}
    src_best: dict[str, Any] | None = None
    if not tokens:
        return best
    for path in sorted(root.rglob("MANIFEST.md"))[:500]:
        try:
            rel = path.relative_to(root).as_posix()
            parent = path.parent.relative_to(root).as_posix()
            text = path.read_text(encoding="utf-8", errors="ignore")[:2500]
        except Exception:
            continue
        hay = _tokens(" ".join([rel, parent, text]))
        score = len(tokens & hay) / max(len(tokens), 1)
        if score > best["confidence"]:
            best = {
                "scope": "root" if parent == "." else parent,
                "manifest_path": rel,
                "confidence": round(score, 4),
            }
        if parent == "src" and (src_best is None or score > src_best["confidence"]):
            src_best = {"scope": "src", "manifest_path": rel, "confidence": round(score, 4)}
    coding_tokens = {"intent", "orchestrator", "context", "injection", "validation", "compile", "fixes", "file"}
    if src_best and tokens & coding_tokens and best["confidence"] - src_best["confidence"] <= 0.12:
        return src_best
    return best


def _stem_key(value: str) -> str:
    stem = Path(value).stem.lower()
    stem = re.sub(r"_s\d{3,4}_v\d{3,4}_.*$", "", stem)
    stem = re.sub(r"_seq\d+.*$", "", stem)
    return re.sub(r"[^a-z0-9_]+", "_", stem).strip("_")


def _tokens(text: str) -> set[str]:
    return set(_token_list(text))


def _token_list(text: str) -> list[str]:
    raw = re.findall(r"[a-zA-Z][a-zA-Z0-9]+", str(text).lower().replace("_", " "))
    out = []
    for token in raw:
        clean = re.sub(r"_+", "_", token).strip("_")
        if len(clean) > 2 and clean not in STOP and clean not in out:
            out.append(clean)
    return out


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def _load_jsonl(path: Path, max_rows: int) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()[:max_rows]:
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
