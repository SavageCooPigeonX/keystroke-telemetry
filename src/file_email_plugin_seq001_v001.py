"""Local file-email comedy plugin.

Files can write local email dispatches when they are touched or selected by
the file-sim compiler. This module does not send SMTP. It writes an outbox
that a later LinkRouter/email pipeline can deliver.
"""
from __future__ import annotations

import html
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import format_datetime, make_msgid
from pathlib import Path
from typing import Any
import urllib.error
import urllib.request

SCHEMA = "file_email/v1"
DEFAULT_CONFIG = {
    "enabled": True,
    "recipient": "context@myaifingerprint.com",
    "sender_domain": "files.local",
    "outbox_dir": "logs/file_email_outbox",
    "context_request_dir": "logs/context_requests",
    "memory_dir": "logs/file_memory",
    "per_fire_limit": 6,
    "write_eml": True,
    "write_markdown": True,
    "tone": "adaptive_mail_memory",
    "triggers": ["file_sim", "touch", "compile", "submission", "completion", "learning_digest", "codex_prompt"],
    "delivery_mode": "resend_dry_run",
    "resend_api_url": "https://api.resend.com/emails",
    "resend_from": "File Comedy <contact@myaifingerprint.com>",
    "resend_user_agent": "keystroke-telemetry-file-email/1.0",
}


def load_file_email_config(root: Path, write_default: bool = True) -> dict[str, Any]:
    root = Path(root)
    path = root / "logs" / "file_email_config.json"
    raw = _load_json(path) if path.exists() else {}
    migrated = False
    if isinstance(raw, dict):
        if raw.get("recipient") in {"operator@local", "context@myaifingerprint"}:
            raw["recipient"] = DEFAULT_CONFIG["recipient"]
            migrated = True
        if raw.get("recipient") == "contact@myaifingerprint.com":
            raw["recipient"] = DEFAULT_CONFIG["recipient"]
            raw["resend_from"] = DEFAULT_CONFIG["resend_from"]
            migrated = True
        if raw.get("resend_from") in {"File Comedy <onboarding@resend.dev>", "contact@myaifingerprint.com"}:
            raw["resend_from"] = DEFAULT_CONFIG["resend_from"]
            migrated = True
        raw_triggers = raw.get("triggers")
        if isinstance(raw_triggers, list):
            merged_triggers = list(dict.fromkeys([*raw_triggers, "submission", "completion", "learning_digest", "codex_prompt"]))
            if merged_triggers != raw_triggers:
                raw["triggers"] = merged_triggers
                migrated = True
    config = merge_file_email_config(raw if isinstance(raw, dict) else {})
    if write_default and (not path.exists() or raw != config or migrated):
        path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(path, config)
    return config


def merge_file_email_config(config: dict[str, Any]) -> dict[str, Any]:
    merged = json.loads(json.dumps(DEFAULT_CONFIG))
    for key, value in (config or {}).items():
        merged[key] = value
    return merged


def emit_file_sim_emails(
    root: Path,
    sim_result: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(root)
    config = merge_file_email_config(config or load_file_email_config(root))
    if not _enabled(config, "file_sim"):
        return {"status": "skipped", "reason": "disabled", "count": 0}
    proposals = sim_result.get("proposals") if isinstance(sim_result.get("proposals"), list) else []
    limit = int(config.get("per_fire_limit") or 6)
    records = []
    if not proposals:
        records.append(emit_file_email(root, event=_monitor_event(sim_result), config=config))
    for proposal in proposals[:limit]:
        records.append(emit_file_email(
            root,
            event={
                "trigger": sim_result.get("trigger", "file_sim"),
                "event_type": "compile",
                "file": proposal.get("path", "unknown"),
                "intent_key": (sim_result.get("intent") or {}).get("intent_key", ""),
                "target_state": sim_result.get("target_state", ""),
                "decision": proposal.get("decision", ""),
                "interlink_score": proposal.get("interlink_score", 0),
                "beef_with": _choose_beef(proposal, proposals),
                "reason": proposal.get("proposed_fix", ""),
                "deepseek_completion_job_id": proposal.get("deepseek_completion_job_id", ""),
                "context_injection": proposal.get("context_injection", []),
                "validation_plan": proposal.get("validation_plan", []),
                "ten_q": proposal.get("ten_q", {}),
                "orchestrator_email_guard": proposal.get("orchestrator_email_guard", {}),
            },
            config=config,
        ))
    return {"status": "ok", "count": len(records), "records": records[:3]}


def emit_learning_digest_email(
    root: Path,
    learning_result: dict[str, Any],
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Emit one narrative operator email from the file self-learning run."""
    root = Path(root)
    config = merge_file_email_config(config or load_file_email_config(root))
    if not _enabled(config, "learning_digest"):
        return {"status": "skipped", "reason": "disabled", "count": 0}
    now = datetime.now(timezone.utc)
    intent = learning_result.get("intent") if isinstance(learning_result.get("intent"), dict) else {}
    wake_order = learning_result.get("wake_order") if isinstance(learning_result.get("wake_order"), list) else []
    packets = learning_result.get("learning_packets") if isinstance(learning_result.get("learning_packets"), list) else []
    top_file = str((wake_order[0] or {}).get("file") if wake_order else "orchestrator/file_self_learning")
    digest = hashlib.sha256(
        json.dumps(
            {
                "intent": intent.get("intent_key"),
                "top_file": top_file,
                "packets": [packet.get("packet_id") for packet in packets[:10] if isinstance(packet, dict)],
                "ts": learning_result.get("ts"),
            },
            sort_keys=True,
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()[:16]
    record = {
        "schema": SCHEMA,
        "ts": now.isoformat(),
        "id": f"file-email:{digest}",
        "trigger": "learning_digest",
        "event_type": "learning_digest",
        "file": "orchestrator/file_self_learning",
        "from": f"file.self.learning@{config.get('sender_domain', 'files.local')}",
        "to": config.get("recipient", "operator@local"),
        "subject": "the files held a rewrite meeting and the grader stole the gavel",
        "beef_with": "grader/master_plan",
        "intent_key": intent.get("intent_key", ""),
        "target_state": learning_result.get("target_state", "interlinked_source_state"),
        "decision": learning_result.get("mode", "learning_only_no_overwrite"),
        "interlink_score": _learning_interlink_score(learning_result),
        "reason": "narrative learning digest for file self-sim orchestration",
        "deepseek_completion_job_id": _learning_packet_summary(packets),
        "context_injection": _learning_context_files(learning_result),
        "validation_plan": _learning_validation_plan(packets),
        "ten_q": _learning_digest_10q(learning_result),
        "orchestrator_email_guard": {
            "schema": "orchestrator_email_guard/v1",
            "aligned": True,
            "decision": "allow_email",
            "policy": "learning_digest_operator_visible",
            "reason": "learning digest is operator-facing control-plane mail",
        },
        "learning_digest": {
            "raw_intent": intent.get("raw", ""),
            "wake_order": wake_order[:12],
            "packets": packets[:12],
            "paths": learning_result.get("paths", {}),
            "backward_learning_pass": learning_result.get("backward_learning_pass", {}),
            "interlink_plan": learning_result.get("interlink_plan", {}),
        },
    }
    record["operator_state"] = _operator_state_snapshot(root, record)
    record["operator_response_policy"] = _response_policy_snapshot(root, record, surface="file_mail_learning_digest")
    record["mail_memory"] = _file_mail_memory_hint(root, config, record)
    record["context_request"] = _write_context_request(root, config, record, record)
    body = render_learning_digest_email(record)
    paths = _write_outbox(root, config, record, body, now)
    (root / "logs" / "file_self_sim_learning_email.md").write_text(body, encoding="utf-8")
    record["paths"] = paths | {"learning_digest": "logs/file_self_sim_learning_email.md"}
    record["mail_memory"] = _write_file_mail_memory(root, config, record, body, paths)
    record["resend"] = _deliver_resend(root, config, record, body)
    _append_jsonl(root / "logs" / "file_email_outbox.jsonl", record)
    return {"status": "ok", "count": 1, "record": record}


def _monitor_event(sim_result: dict[str, Any]) -> dict[str, Any]:
    intent_key = (sim_result.get("intent") or {}).get("intent_key", "")
    ten_q = {
        "schema": "file_consensus_10q/v1",
        "score": 4,
        "max_score": 10,
        "min_score": 7,
        "passed": False,
        "reason": "no source file proposals were selected",
        "checks": [
            {"key": "intent_alignment", "passed": bool(intent_key), "reason": "intent compiled" if intent_key else "intent did not compile"},
            {"key": "source_target", "passed": False, "reason": "no source target selected"},
            {"key": "context_available", "passed": bool((sim_result.get("distributed_intent_encoding") or {}).get("file_votes")), "reason": "numeric context inspected"},
            {"key": "validation_plan", "passed": False, "reason": "no file-specific validation plan"},
            {"key": "operator_approval", "passed": True, "reason": "operator approval is required"},
            {"key": "deepseek_job_allowed", "passed": False, "reason": "DeepSeek job blocked without file target"},
            {"key": "incompatibility_known", "passed": True, "reason": "no peer proposals to conflict"},
            {"key": "identity_growth", "passed": False, "reason": "no file identity grew"},
            {"key": "dirty_state_known", "passed": True, "reason": "sim self model inspected dirty files"},
            {"key": "file_exists", "passed": False, "reason": "no file target exists"},
        ],
    }
    return {
        "trigger": sim_result.get("trigger", "file_sim"),
        "event_type": "compile",
        "file": "orchestrator/prompt_monitor",
        "intent_key": intent_key,
        "target_state": sim_result.get("target_state", "interlinked_source_state"),
        "decision": "no_file_proposals",
        "interlink_score": 0,
        "beef_with": "candidate_ranker",
        "reason": "prompt fired through orchestrator, but no source files were selected; request more context before rewrite",
        "deepseek_completion_job_id": "blocked_by_no_file_candidates",
        "context_injection": ["logs/batch_rewrite_sim_latest.json", "logs/dynamic_context_pack.json"],
        "validation_plan": ["review prompt intent", "add manifest/context target", "rerun file sim"],
        "ten_q": ten_q,
        "orchestrator_email_guard": {
            "schema": "orchestrator_email_guard/v1",
            "aligned": False,
            "decision": "local_only",
            "policy": "block_resend_when_failed",
            "reason": "10Q consensus failed: no source file proposals were selected",
        },
    }


def emit_touch_email(
    root: Path,
    file_path: str,
    why: str = "codex edit",
    prompt: str = "",
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(root)
    config = merge_file_email_config(config or load_file_email_config(root))
    if not _enabled(config, "touch"):
        return {"status": "skipped", "reason": "disabled"}
    return emit_file_email(
        root,
        event={
            "trigger": "touch",
            "event_type": "touch",
            "file": file_path or "unknown",
            "intent_key": "",
            "target_state": "interlinked_source_state",
            "decision": "touched",
            "interlink_score": 0,
            "beef_with": _touch_beef(file_path, prompt),
            "reason": why,
            "prompt": prompt[:400],
            "context_injection": [],
            "validation_plan": ["git diff --check"],
        },
        config=config,
    )


def emit_prompt_lifecycle_email(
    root: Path,
    loop: dict[str, Any],
    phase: str = "submission",
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(root)
    phase = "completion" if phase == "completion" else "submission"
    config = merge_file_email_config(config or load_file_email_config(root))
    if not _enabled(config, phase):
        return {"status": "skipped", "reason": "disabled", "phase": phase}
    return emit_file_email(root, event=_lifecycle_event(loop, phase), config=config)


def emit_codex_prompt_email(
    root: Path,
    prompt_entry: dict[str, Any],
    loop: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Emit the one-per-Codex-prompt operator receipt.

    This is intentionally local/dev-control-plane mail, not Hush/web-chat mail.
    """
    root = Path(root)
    config = merge_file_email_config(config or load_file_email_config(root))
    if not _enabled(config, "codex_prompt"):
        return {"status": "skipped", "reason": "disabled", "phase": "codex_prompt"}
    loop = loop if isinstance(loop, dict) else {}
    prompt = str(prompt_entry.get("msg") or prompt_entry.get("prompt") or "").strip()
    context = prompt_entry.get("context_selection") if isinstance(prompt_entry.get("context_selection"), dict) else {}
    file_sim = prompt_entry.get("file_sim") if isinstance(prompt_entry.get("file_sim"), dict) else {}
    focus_files = _codex_prompt_focus_files(context, file_sim, loop)
    source = str(prompt_entry.get("source") or loop.get("source") or "codex")
    intent_key = str(loop.get("intent_key") or ((file_sim.get("intent") or {}).get("intent_key") if isinstance(file_sim.get("intent"), dict) else "") or prompt_entry.get("intent") or "codex:prompt:receipt")
    event = {
        "trigger": "codex_prompt",
        "event_type": "codex_prompt",
        "file": "orchestrator/codex_prompt",
        "intent_key": intent_key,
        "target_state": "codex_prompt_operator_receipt",
        "decision": "prompt_received",
        "interlink_score": context.get("confidence", 0),
        "beef_with": loop.get("loop_id") or "missing_codex_prompt_receipt",
        "reason": _codex_prompt_reason(prompt_entry, prompt, source, loop),
        "deepseek_completion_job_id": _codex_prompt_job_id(file_sim),
        "context_injection": focus_files[:10] or ["logs/prompt_journal.jsonl", "logs/intent_loop_latest.json"],
        "validation_plan": [
            "prompt receipt recorded",
            "operator-visible Codex email emitted",
            "intent loop remains approval gated",
        ],
        "ten_q": _codex_prompt_ten_q(prompt, source, loop),
        "orchestrator_email_guard": _codex_prompt_guard(),
    }
    return emit_file_email(root, event=event, config=config)


def _codex_prompt_focus_files(
    context: dict[str, Any],
    file_sim: dict[str, Any],
    loop: dict[str, Any],
) -> list[str]:
    out: list[str] = []
    for proposal in file_sim.get("proposals") or []:
        if isinstance(proposal, dict) and proposal.get("path"):
            out.append(str(proposal.get("path")))
    for item in context.get("files") or []:
        if isinstance(item, dict) and item.get("name"):
            out.append(str(item.get("name")))
        elif isinstance(item, str):
            out.append(item)
    for item in loop.get("focus_files") or []:
        if item:
            out.append(str(item))
    out.extend(["logs/prompt_journal.jsonl", "logs/intent_loop_latest.json"])
    return _dedupe_list([item for item in out if item])[:16]


def _codex_prompt_job_id(file_sim: dict[str, Any]) -> str:
    for proposal in file_sim.get("proposals") or []:
        if isinstance(proposal, dict) and proposal.get("deepseek_completion_job_id"):
            return str(proposal.get("deepseek_completion_job_id"))
    return ""


def _codex_prompt_reason(
    prompt_entry: dict[str, Any],
    prompt: str,
    source: str,
    loop: dict[str, Any],
) -> str:
    session_n = prompt_entry.get("session_n")
    loop_id = loop.get("loop_id") or "no_loop_yet"
    preview = _plain_snip(prompt, 260) or "empty prompt"
    return f"Codex prompt receipt from `{source}` session `{session_n}` loop `{loop_id}`: {preview}"


def _codex_prompt_ten_q(prompt: str, source: str, loop: dict[str, Any]) -> dict[str, Any]:
    checks = [
        {"key": "prompt_present", "passed": bool(prompt), "reason": "Codex prompt text captured" if prompt else "prompt was empty"},
        {"key": "operator_visible", "passed": True, "reason": "receipt is addressed to the configured operator mailbox"},
        {"key": "control_plane_only", "passed": True, "reason": "emitted from codex_compat/local hook, not web chat"},
        {"key": "intent_loop_bound", "passed": bool(loop.get("loop_id")), "reason": "intent loop id attached" if loop.get("loop_id") else "receipt can send before loop id exists"},
        {"key": "human_on_loop", "passed": loop.get("human_position", "on_loop") == "on_loop", "reason": "operator keeps approve/veto position"},
        {"key": "no_auto_write", "passed": not bool(loop.get("auto_write_allowed")), "reason": "prompt mail does not grant autonomous overwrite"},
        {"key": "source_codex", "passed": "codex" in source.lower() or source in {"pre_prompt", "os_hook_auto", "composition"}, "reason": f"source `{source}` is a Codex/dev prompt surface"},
        {"key": "outbox_written", "passed": True, "reason": "local outbox is always written before delivery"},
        {"key": "delivery_guard", "passed": True, "reason": "operator requested Codex prompt receipts"},
        {"key": "reply_path", "passed": True, "reason": "mail memory accepts remember/use/avoid/style replies"},
    ]
    return {
        "schema": "codex_prompt_receipt_10q/v1",
        "score": sum(1 for item in checks if item["passed"]),
        "max_score": len(checks),
        "min_score": 7,
        "passed": bool(prompt),
        "reason": "Codex prompt receipt ready for operator" if prompt else "empty prompt skipped from real delivery",
        "checks": checks,
    }


def _codex_prompt_guard() -> dict[str, Any]:
    return {
        "schema": "orchestrator_email_guard/v1",
        "aligned": True,
        "decision": "allow_email",
        "policy": "codex_prompt_operator_receipt",
        "reason": "operator requested one email per Codex prompt",
    }


def email_delivery_status(root: Path, config: dict[str, Any] | None = None) -> dict[str, Any]:
    root = Path(root)
    _load_local_email_env(root)
    config = merge_file_email_config(config or load_file_email_config(root))
    latest = _load_json(root / "logs" / "resend_payload_latest.json") or {}
    mode = os.environ.get("FILE_EMAIL_DELIVERY") or str(config.get("delivery_mode") or "resend_dry_run")
    blockers = []
    if mode != "resend":
        blockers.append("delivery_mode_is_not_resend")
    if not os.environ.get("RESEND_API_KEY"):
        blockers.append("missing_RESEND_API_KEY")
    status = {
        "schema": "file_email_delivery_status/v1",
        "ts": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "can_send": mode == "resend" and bool(os.environ.get("RESEND_API_KEY")),
        "api_key_present": bool(os.environ.get("RESEND_API_KEY")),
        "from": os.environ.get("RESEND_FROM") or str(config.get("resend_from") or DEFAULT_CONFIG["resend_from"]),
        "recipient": config.get("recipient") or DEFAULT_CONFIG["recipient"],
        "api_url": config.get("resend_api_url") or DEFAULT_CONFIG["resend_api_url"],
        "user_agent": os.environ.get("RESEND_USER_AGENT") or str(config.get("resend_user_agent") or DEFAULT_CONFIG["resend_user_agent"]),
        "blockers": blockers,
        "latest_payload": {
            "mode": latest.get("mode"),
            "api_key_present": latest.get("api_key_present"),
            "guard_decision": ((latest.get("orchestrator_guard") or {}).get("decision")),
            "email_id": latest.get("email_id"),
            "ts": latest.get("ts"),
        } if isinstance(latest, dict) else {},
        "how_to_enable": [
            "Set FILE_EMAIL_DELIVERY=resend",
            "Set RESEND_API_KEY",
            "Optionally set RESEND_FROM='File Comedy <contact@myaifingerprint.com>'",
        ],
    }
    _write_json(root / "logs" / "file_email_delivery_status.json", status)
    return status


def _lifecycle_event(loop: dict[str, Any], phase: str) -> dict[str, Any]:
    proposals = loop.get("proposals") if isinstance(loop.get("proposals"), list) else []
    best = proposals[0] if proposals else {}
    ten_q = _lifecycle_ten_q(loop, phase, best)
    guard = _lifecycle_guard(ten_q, phase)
    file_name = "orchestrator/prompt_submission" if phase == "submission" else "orchestrator/intent_completion"
    jobs = [
        str(item.get("deepseek_job_id") or "")
        for item in proposals
        if isinstance(item, dict) and item.get("deepseek_job_id")
    ]
    focus_files = loop.get("focus_files") if isinstance(loop.get("focus_files"), list) else []
    observed_edits = loop.get("observed_edits") if isinstance(loop.get("observed_edits"), list) else []
    return {
        "trigger": phase,
        "event_type": phase,
        "file": file_name,
        "intent_key": loop.get("intent_key", ""),
        "target_state": loop.get("target_state", "interlinked_source_state"),
        "decision": loop.get("status", ""),
        "interlink_score": best.get("interlink_score", 0),
        "beef_with": "operator_approval" if phase == "submission" else "validation_gate",
        "reason": _lifecycle_reason(loop, phase),
        "deepseek_completion_job_id": jobs[0] if jobs else "",
        "context_injection": focus_files[:10],
        "validation_plan": _lifecycle_validation(loop, phase, observed_edits),
        "ten_q": ten_q,
        "orchestrator_email_guard": guard,
    }


def _lifecycle_reason(loop: dict[str, Any], phase: str) -> str:
    prompt = str(loop.get("prompt") or "")[:220]
    if phase == "completion":
        note = str(loop.get("completion_note") or "completion recorded")
        return f"intent loop completed: {note}; prompt: {prompt}"
    return f"prompt submitted into intent loop; human remains on-loop; prompt: {prompt}"


def _lifecycle_validation(loop: dict[str, Any], phase: str, observed_edits: list[dict[str, Any]]) -> list[str]:
    if phase == "completion":
        files = [str(item.get("file")) for item in observed_edits[:6] if isinstance(item, dict) and item.get("file")]
        checks = ["completion receipt recorded", "training candidate generated"]
        checks.extend(f"review bound edit `{file_name}`" for file_name in files)
        return checks[:8]
    return [
        "prompt receipt recorded",
        "intent loop ticket written",
        "dynamic context pack injected",
        "operator approval required before overwrite",
    ]


def _lifecycle_ten_q(loop: dict[str, Any], phase: str, best: dict[str, Any]) -> dict[str, Any]:
    if isinstance(best.get("ten_q"), dict) and best["ten_q"]:
        return best["ten_q"]
    proposals = loop.get("proposals") if isinstance(loop.get("proposals"), list) else []
    observed_edits = loop.get("observed_edits") if isinstance(loop.get("observed_edits"), list) else []
    closed = str(loop.get("status") or "") in {"verified", "done", "resolved"}
    checks = [
        {"key": "intent_alignment", "passed": bool(loop.get("intent_key")), "reason": "intent loop has an intent key"},
        {"key": "context_available", "passed": bool(loop.get("focus_files")), "reason": "focus files/context selected"},
        {"key": "source_target", "passed": bool(proposals or observed_edits), "reason": "source proposal or bound edit exists"},
        {"key": "validation_plan", "passed": phase == "submission" or closed, "reason": "submission is gated; completion requires verified close"},
        {"key": "operator_approval", "passed": bool(loop.get("approval_required", True)), "reason": "operator approval remains required"},
        {"key": "completion_bound", "passed": phase == "submission" or bool(observed_edits), "reason": "completion has bound edits" if observed_edits else "no bound edits yet"},
        {"key": "training_candidate", "passed": phase == "submission" or bool(observed_edits), "reason": "bound edits can train future routing" if observed_edits else "awaiting execution"},
        {"key": "stale_date_guard", "passed": bool(loop.get("updated_ts") or loop.get("ts")), "reason": "loop timestamp exists"},
        {"key": "human_on_loop", "passed": loop.get("human_position") == "on_loop", "reason": "human is approval/veto, not hidden in-loop"},
        {"key": "no_autowrite", "passed": not bool(loop.get("auto_write_allowed")), "reason": "autonomous overwrite is blocked"},
    ]
    score = sum(1 for item in checks if item["passed"])
    return {
        "schema": "prompt_lifecycle_10q/v1",
        "score": score,
        "max_score": 10,
        "min_score": 7,
        "passed": score >= 7,
        "reason": "passed" if score >= 7 else "prompt lifecycle needs more bound evidence",
        "checks": checks,
    }


def _lifecycle_guard(ten_q: dict[str, Any], phase: str) -> dict[str, Any]:
    aligned = bool(ten_q.get("passed"))
    return {
        "schema": "orchestrator_email_guard/v1",
        "aligned": aligned,
        "decision": "allow_email" if aligned else "local_only",
        "policy": "prompt_lifecycle_local_first",
        "reason": f"{phase} lifecycle 10Q {'passed' if aligned else 'failed'}",
    }


def emit_file_email(root: Path, event: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
    root = Path(root)
    config = merge_file_email_config(config or load_file_email_config(root))
    now = datetime.now(timezone.utc)
    file_path = str(event.get("file") or "unknown")
    beef_with = str(event.get("beef_with") or "the last file that touched global state")
    digest = hashlib.sha256(json.dumps(event, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]
    record = {
        "schema": SCHEMA,
        "ts": now.isoformat(),
        "id": f"file-email:{digest}",
        "trigger": event.get("trigger", "manual"),
        "event_type": event.get("event_type", "touch"),
        "file": file_path,
        "from": f"{_safe_mailbox(Path(file_path).stem)}@{config.get('sender_domain', 'files.local')}",
        "to": config.get("recipient", "operator@local"),
        "subject": _subject(file_path, beef_with, event),
        "beef_with": beef_with,
        "intent_key": event.get("intent_key", ""),
        "target_state": event.get("target_state", ""),
        "decision": event.get("decision", ""),
        "interlink_score": event.get("interlink_score", 0),
        "reason": event.get("reason", ""),
        "deepseek_completion_job_id": event.get("deepseek_completion_job_id", ""),
        "context_injection": event.get("context_injection", []),
        "validation_plan": event.get("validation_plan", []),
        "ten_q": event.get("ten_q", {}),
        "orchestrator_email_guard": event.get("orchestrator_email_guard", {}),
    }
    record["operator_state"] = _operator_state_snapshot(root, event)
    record["operator_response_policy"] = _response_policy_snapshot(root, event, surface="file_mail")
    record["mail_memory"] = _file_mail_memory_hint(root, config, record)
    record["context_request"] = _write_context_request(root, config, record, event)
    body = render_file_email(record)
    paths = _write_outbox(root, config, record, body, now)
    record["paths"] = paths
    record["mail_memory"] = _write_file_mail_memory(root, config, record, body, paths)
    record["resend"] = _deliver_resend(root, config, record, body)
    _append_jsonl(root / "logs" / "file_email_outbox.jsonl", record)
    return record


def render_file_email(record: dict[str, Any]) -> str:
    file_path = record.get("file", "unknown")
    beef = record.get("beef_with", "unknown")
    operator = record.get("operator_state") if isinstance(record.get("operator_state"), dict) else {}
    policy = record.get("operator_response_policy") if isinstance(record.get("operator_response_policy"), dict) else {}
    memory = record.get("mail_memory") if isinstance(record.get("mail_memory"), dict) else {}
    failed_checks = _failed_checks(record)
    lines = [
        f"From: {file_path}",
        f"To: Nikita",
        f"Subject: {record.get('subject', '')}",
        "",
        f"{operator.get('operator_name') or 'Nikita'},",
        "",
        _actionable_mail_opening(file_path, record, operator, memory, failed_checks),
        _policy_mail_line(policy),
        "",
        "I learned:",
        *_prefixed(_learned_lines(file_path, record, operator, memory), "- "),
        "",
        "I did:",
        *_prefixed(_done_lines(file_path, record, operator, memory), "- "),
        "",
        "Next I am planning:",
        *_prefixed(_planning_lines(file_path, record, operator, memory, failed_checks), "- "),
        "",
        "I need from you:",
        *_prefixed(_need_lines(file_path, record, memory, failed_checks), "- "),
        "",
        "Tiny bit of file gossip:",
        _actionable_comedy_line(file_path, beef, record, operator, memory, failed_checks),
        "",
        "Memory thread:",
        f"- `{memory.get('markdown') or memory.get('path') or 'logs/file_memory'}`",
        f"- message: `{memory.get('message_count', 0)}`",
        f"- reply syntax: `remember: ...`, `use: ...`, `avoid: ...`, `style: ...`",
        "",
        "Router receipt, because tools still need a handle:",
        f"- operator intent: `{operator.get('primary_operator_intent') or 'unknown'}`",
        f"- intent: `{record.get('intent_key') or operator.get('operator_intent_key') or 'none'}`",
        f"- context request: `{(record.get('context_request') or {}).get('request_id', 'none')}`",
        f"- validation: `{_first_validation(record)}`",
    ]
    if failed_checks:
        lines.append(f"- failed: `{_failed_check_summary(failed_checks)}`")
    else:
        lines.append("- failed checks: none")
    lines.append("")
    return "\n".join(lines)


def render_learning_digest_email(record: dict[str, Any]) -> str:
    digest = record.get("learning_digest") if isinstance(record.get("learning_digest"), dict) else {}
    operator = record.get("operator_state") if isinstance(record.get("operator_state"), dict) else {}
    policy = record.get("operator_response_policy") if isinstance(record.get("operator_response_policy"), dict) else {}
    wake_order = digest.get("wake_order") if isinstance(digest.get("wake_order"), list) else []
    packets = digest.get("packets") if isinstance(digest.get("packets"), list) else []
    top = wake_order[0] if wake_order else {}
    second = wake_order[1] if len(wake_order) > 1 else {}
    third = wake_order[2] if len(wake_order) > 2 else {}
    validation = _learning_validation_plan(packets)
    context = _learning_context_from_record(record)
    current = _learning_current_work(record) or operator.get("current_work") or "make the files earn their own rewrite"
    profile_note = _learning_profile_signal_line(record, operator)
    lines = [
        f"From: {record.get('file')}",
        "To: Nikita",
        f"Subject: {record.get('subject', '')}",
        "",
        "Nikita,",
        "",
        _policy_mail_line(policy),
        "",
        "The repo called an emergency rewrite meeting and immediately lied about being ready.",
        "",
        f"`{Path(str(top.get('file') or 'the top file')).name}` kicked the door open first because `{top.get('wake_reason', 'the intent math pointed at it')}`.",
    ]
    if second:
        lines.append(
            f"`{Path(str(second.get('file'))).name}` followed with a stack of receipts and the facial expression of a file that has seen a stale context pack ruin lunch."
        )
    if third:
        lines.append(
            f"`{Path(str(third.get('file'))).name}` said it was just here to help, which everyone correctly understood as a threat to reorganize the room."
        )
    lines.extend([
        "",
        "Then the grader walked in, stole the marker, and wrote one sentence on the board:",
        "",
        "\"No overwrite until the validation packet can survive daylight.\"",
        "",
        "That is the master plan. The grader is not comic relief. The grader is the bouncer, the accountant, and the little courtroom in the wall. Every file can monologue. Only the grader gets to say whether the monologue becomes source.",
        "",
        "What I think you are actually doing:",
        f"{current}.",
    ])
    if profile_note:
        lines.extend(["", profile_note])
    lines.extend([
        "",
        "What the files learned while arguing:",
        *_learning_story_lessons(wake_order, packets),
        "",
        "Overheard in the file room:",
        *_learning_story_quotes(wake_order, packets),
        "",
        "Who wants the next job:",
        *_learning_story_cast(wake_order, packets),
        "",
        "What DeepSeek should receive, if we let it near the keyboard:",
        *_learning_story_deepseek(packets, context, validation),
        "",
        "What the grader will accept:",
        *_learning_story_grader(validation),
        "",
        "What I need from you, not as a form, as control:",
        "- `approve: draft tests` if the next move is letting the files write their own proof.",
        "- `use: path/to/file.py` if a context vein is missing and you want it loaded every time.",
        "- `avoid: stale committee email` if this voice starts wearing a blazer again.",
        "- `style: narrative comedy, files have grudges, grader has veto` if this is the lane.",
        "",
        "Routing crumbs under the floorboards:",
        f"- intent: `{record.get('intent_key') or 'none'}`",
        f"- context request: `{(record.get('context_request') or {}).get('request_id', 'none')}`",
        f"- learning packets: `{_learning_packet_summary(packets)}`",
        f"- latest sim: `{(digest.get('paths') or {}).get('latest', 'logs/file_self_sim_learning_latest.json')}`",
        f"- profile memory: `file_profiles.json`",
        "",
        "Closing scene:",
        _learning_closing_scene(wake_order, packets),
        "",
    ])
    return "\n".join(lines)


def _response_policy_snapshot(root: Path, event: dict[str, Any], surface: str = "file_mail") -> dict[str, Any]:
    prompt = " ".join(
        str(event.get(key) or "")
        for key in ("prompt", "reason", "intent_key", "target_state")
        if event.get(key)
    ).strip()
    try:
        from src.operator_response_policy_seq001_v001 import build_operator_response_policy
        policy = build_operator_response_policy(
            root,
            prompt=prompt,
            surface=surface,
            context_pack={},
            inject=False,
            write=True,
        )
        return {
            "schema": policy.get("schema"),
            "ts": policy.get("ts"),
            "active_arm": policy.get("active_arm"),
            "operator_read": policy.get("operator_read"),
            "required_sections": policy.get("required_sections", []),
            "intent_moves": policy.get("intent_moves", [])[:5],
            "probe_files": policy.get("probe_files", [])[:8],
            "next_mutation": policy.get("next_mutation", ""),
            "recent_reward": policy.get("recent_reward", {}),
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc), "active_arm": "old_friend_file_mail"}


def _policy_mail_line(policy: dict[str, Any]) -> str:
    if not policy:
        return ""
    arm = policy.get("active_arm") or "old_friend_file_mail"
    read = _plain_snip(policy.get("operator_read"), 180)
    if arm == "quiet_checkpoint":
        return f"Response policy: `{arm}`. I am keeping this calm: {read}"
    if arm == "surgical_engineer":
        return f"Response policy: `{arm}`. Action first, proof second: {read}"
    if arm == "chaos_comedy":
        return f"Response policy: `{arm}`. The jokes are on probation until the next mutation has receipts: {read}"
    return f"Response policy: `{arm}`. Operator read first: {read}"


def _prefixed(values: list[str], prefix: str) -> list[str]:
    return [prefix + value for value in values if value]


def _learning_interlink_score(learning_result: dict[str, Any]) -> float:
    wake_order = learning_result.get("wake_order") if isinstance(learning_result.get("wake_order"), list) else []
    if not wake_order:
        return 0.0
    scores = [float(item.get("wake_score") or 0) for item in wake_order if isinstance(item, dict)]
    return round(min(1.0, sum(scores[:6]) / max(1.0, len(scores[:6]) * 12.0)), 3)


def _learning_packet_summary(packets: list[dict[str, Any]]) -> str:
    ids = [str(packet.get("packet_id")) for packet in packets if isinstance(packet, dict) and packet.get("packet_id")]
    if not ids:
        return "no_packets"
    return f"{len(ids)} packet(s): " + ", ".join(ids[:4])


def _learning_context_files(learning_result: dict[str, Any]) -> list[str]:
    out = []
    plan = learning_result.get("interlink_plan") if isinstance(learning_result.get("interlink_plan"), dict) else {}
    for job in plan.get("near_term_jobs") or []:
        if isinstance(job, dict):
            out.extend(str(item) for item in job.get("files") or [])
    for node in learning_result.get("wake_order") or []:
        if isinstance(node, dict):
            out.append(str(node.get("file") or ""))
            out.extend(str(item.get("file") or "") for item in node.get("context_veins") or [] if isinstance(item, dict))
    return [item for item in _dedupe_list([item for item in out if item])[:16]]


def _learning_validation_plan(packets: list[dict[str, Any]]) -> list[str]:
    out = []
    for packet in packets:
        if not isinstance(packet, dict):
            continue
        verification = packet.get("verification_packet") if isinstance(packet.get("verification_packet"), dict) else {}
        out.extend(str(item) for item in verification.get("validation_plan") or [])
    return _dedupe_list([item for item in out if item])[:8]


def _learning_digest_10q(learning_result: dict[str, Any]) -> dict[str, Any]:
    wake_order = learning_result.get("wake_order") if isinstance(learning_result.get("wake_order"), list) else []
    packets = learning_result.get("learning_packets") if isinstance(learning_result.get("learning_packets"), list) else []
    validation = _learning_validation_plan(packets)
    checks = [
        _digest_check("intent_alignment", bool((learning_result.get("intent") or {}).get("intent_key")), "intent key compiled", "intent key missing"),
        _digest_check("wake_order", bool(wake_order), "files woke for the prompt", "no files woke"),
        _digest_check("learning_packets", bool(packets), "DeepSeek learning packets exist", "no learning packets emitted"),
        _digest_check("validation_plan", bool(validation), "validation gates are named", "validation gates missing"),
        _digest_check("operator_visible", True, "narrative email is operator-facing", "not visible to operator"),
        _digest_check("no_auto_overwrite", learning_result.get("mode") == "learning_only_no_overwrite", "source overwrite blocked", "overwrite mode is unsafe"),
        _digest_check("profile_memory", True, "file profile memory receives learning state", "profile memory missing"),
        _digest_check("deepseek_context", bool(_learning_context_files(learning_result)), "context pack can be assembled", "context pack missing"),
        _digest_check("grader_veto", True, "grader owns execution veto", "grader not attached"),
        _digest_check("reply_path", True, "operator can reply with approve/use/avoid/style", "reply path missing"),
    ]
    score = sum(1 for item in checks if item.get("passed"))
    return {
        "schema": "file_consensus_10q/v1",
        "score": score,
        "max_score": len(checks),
        "min_score": 7,
        "passed": score >= 7,
        "reason": "learning digest ready for operator" if score >= 7 else "learning digest missing required routing facts",
        "checks": checks,
    }


def _digest_check(key: str, passed: bool, pass_reason: str, fail_reason: str) -> dict[str, Any]:
    return {"key": key, "passed": bool(passed), "reason": pass_reason if passed else fail_reason}


def _learning_context_from_record(record: dict[str, Any]) -> list[str]:
    return [str(item) for item in (record.get("context_injection") or []) if item][:12]


def _learning_current_work(record: dict[str, Any]) -> str:
    digest = record.get("learning_digest") if isinstance(record.get("learning_digest"), dict) else {}
    raw = re.sub(r"\s+", " ", str(digest.get("raw_intent") or "")).strip()
    if raw:
        return _plain_snip(raw, 260)
    intent_key = str(record.get("intent_key") or "compiled intent")
    return (
        "training small files to wake by encoded intent, argue through context, write tests, "
        f"and earn self-overwrite later under `{intent_key}`"
    )


def _learning_profile_signal_line(record: dict[str, Any], operator: dict[str, Any]) -> str:
    latest = _plain_snip(operator.get("latest_operator_text"), 220)
    if not latest:
        return ""
    digest = record.get("learning_digest") if isinstance(record.get("learning_digest"), dict) else {}
    raw = str(digest.get("raw_intent") or "")
    if raw and _token_overlap_ratio(raw, latest) < 0.25:
        return f"Profile cache note: \"{latest}\" looks stale for this sim, so the files ignored it and used the live intent."
    return f"Latest operator signal: \"{latest}\""


def _token_overlap_ratio(left: str, right: str) -> float:
    left_tokens = set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", str(left).lower()))
    right_tokens = set(re.findall(r"[a-zA-Z_][a-zA-Z0-9_]*", str(right).lower()))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / max(1, min(len(left_tokens), len(right_tokens)))


def _learning_story_lessons(wake_order: list[dict[str, Any]], packets: list[dict[str, Any]]) -> list[str]:
    lessons = []
    if wake_order:
        top = wake_order[0]
        lessons.append(
            f"- `{Path(str(top.get('file'))).name}` learned it is the first suspect, not the hero. Wake score `{top.get('wake_score')}` buys attention, not permission."
        )
    if packets:
        first_packet = packets[0]
        readiness = first_packet.get("overwrite_readiness") if isinstance(first_packet.get("overwrite_readiness"), dict) else {}
        lessons.append(
            f"- `{Path(str(first_packet.get('file'))).name}` tried to sound rewrite-ready. The grader read `{readiness.get('state', 'unknown')}` and put the chair back under the table."
        )
    if len(packets) > 1:
        lessons.append(
            f"- `{len(packets)}` files now have packet-shaped memory. That means future prompts can reuse scars instead of rediscovering the same rake."
        )
    if not lessons:
        lessons.append("- The meeting learned nothing, which is useful because now candidate selection is the problem.")
    return lessons[:4]


def _learning_story_quotes(wake_order: list[dict[str, Any]], packets: list[dict[str, Any]]) -> list[str]:
    packet_by_file = {
        str(packet.get("file")): packet
        for packet in packets
        if isinstance(packet, dict) and packet.get("file")
    }
    quotes = []
    for node in wake_order[:8]:
        file_path = str(node.get("file") or "unknown")
        packet = packet_by_file.get(file_path, {})
        role = str(node.get("role") or "learner")
        validation = _learning_validation_plan([packet]) if packet else []
        readiness = packet.get("overwrite_readiness") if isinstance(packet.get("overwrite_readiness"), dict) else {}
        quote = _file_state_quote(file_path, role, validation, readiness, node)
        quotes.append(f"- `{Path(file_path).name}`: \"{quote}\"")
    return quotes or ["- `orchestrator`: \"No file spoke. The selector is standing in the corner pretending that was a strategy.\""]


def _file_state_quote(
    file_path: str,
    role: str,
    validation: list[str],
    readiness: dict[str, Any],
    node: dict[str, Any],
) -> str:
    name = Path(file_path).name
    gate = validation[0] if validation else str(node.get("next_question") or "bring me a real validation gate")
    state = readiness.get("state") or "unscored"
    if role == "top_waker":
        return f"I woke first, which means I am the smoke alarm, not the mayor. Run `{gate}` before anyone hands me a rewrite helmet."
    if role == "validator":
        return f"I brought the receipt printer. If `{gate}` does not pass, everyone can stop doing interpretive architecture."
    if role == "diagnoser":
        return f"I can explain the wound, but `{state}` means the grader still has me on a leash made of tests."
    if role == "manifest_anchor":
        return "I am the constitution with a filename. If the scope drifts, I will make it everyone's personality problem."
    if "test" in name:
        return f"I am here to ruin false confidence at `{gate}` and I packed a lunch."
    return f"I have a packet, a grudge, and `{state}` stamped on my forehead. Feed me context or enjoy premium nonsense."


def _learning_story_cast(wake_order: list[dict[str, Any]], packets: list[dict[str, Any]]) -> list[str]:
    packet_by_file = {
        str(packet.get("file")): packet
        for packet in packets
        if isinstance(packet, dict) and packet.get("file")
    }
    lines = []
    for node in wake_order[:5]:
        file_path = str(node.get("file") or "unknown")
        packet = packet_by_file.get(file_path, {})
        validation = _learning_validation_plan([packet]) if packet else []
        role = node.get("role", "learner")
        next_q = node.get("next_question", "ask the grader what proof is missing")
        lines.append(
            f"- `{Path(file_path).name}` as `{role}`: wants `{validation[0] if validation else next_q}` before anyone touches source."
        )
    return lines or ["- No cast formed. The ranker owes you a better audition."]


def _learning_story_deepseek(
    packets: list[dict[str, Any]],
    context: list[str],
    validation: list[str],
) -> list[str]:
    if not packets:
        return ["- Nothing yet. DeepSeek gets no prompt until a file earns the stage."]
    top = packets[0]
    lines = [
        f"- File: `{top.get('file')}`",
        f"- Packet: `{top.get('packet_id')}`",
        f"- Load first: `{', '.join(context[:5]) or 'context still thin'}`",
        f"- Do not draft a full overwrite. Draft diagnosis, smallest patch hypothesis, risk, and the test it must survive.",
    ]
    if validation:
        lines.append(f"- First grader demand: `{validation[0]}`")
    return lines


def _learning_story_grader(validation: list[str]) -> list[str]:
    if not validation:
        return ["- No tests, no crown. The grader refuses to certify vibes."]
    return [
        f"- `{validation[0]}` passes.",
        "- A context pack exists and is not stale.",
        "- The file can explain what it learned after success or failure.",
        "- The backward-learning pass writes the reward into `file_profiles.json`.",
    ]


def _learning_closing_scene(wake_order: list[dict[str, Any]], packets: list[dict[str, Any]]) -> str:
    if not wake_order:
        return "No one woke up. That is not mysterious. That is the selector asking to be fixed in public."
    top = Path(str(wake_order[0].get("file") or "top file")).name
    packet_count = len(packets)
    return (
        f"`{top}` is standing at the front with {packet_count} packet(s) behind it, "
        "trying to look brave. The grader is smiling like a locked door. Perfect. That is the shape."
    )


def _all_checks(record: dict[str, Any]) -> list[dict[str, Any]]:
    ten_q = record.get("ten_q") if isinstance(record.get("ten_q"), dict) else {}
    checks = ten_q.get("checks") if isinstance(ten_q.get("checks"), list) else []
    return [item for item in checks if isinstance(item, dict)]


def _failed_checks(record: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in _all_checks(record) if not item.get("passed")]


def _passed_checks(record: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in _all_checks(record) if item.get("passed")]


def _format_check_line(item: dict[str, Any], label: str | None = None) -> str:
    status = label or ("PASS" if item.get("passed") else "FAIL")
    return f"- `{status}` `{item.get('key', 'unknown')}` - {item.get('reason', 'no reason attached')}"


def _actionable_mail_opening(
    file_path: str,
    record: dict[str, Any],
    operator: dict[str, Any],
    memory: dict[str, Any],
    failed_checks: list[dict[str, Any]],
) -> str:
    file_name = Path(file_path).name
    current = operator.get("current_work") or "make file mail actionable"
    if failed_checks:
        return (
            f"Okay, real note from `{file_name}`: I learned the goal, I found the snag, "
            "and I am not going to bury it in polite dashboard soup."
        )
    if memory.get("message_count", 0) > 1:
        return (
            f"Okay, real note from `{file_name}`: this thread has memory now. "
            f"I am using it to help with `{current}` instead of sending decorative status confetti."
        )
    return (
        f"Okay, real note from `{file_name}`: I am making this actionable. "
        f"The live job is `{current}`, and this email is the working memory crumb."
    )


def _learned_lines(
    file_path: str,
    record: dict[str, Any],
    operator: dict[str, Any],
    memory: dict[str, Any],
) -> list[str]:
    knowledge = _memory_knowledge(memory)
    lines = []
    current = operator.get("current_work")
    latest = _plain_snip(operator.get("latest_operator_text"), 160)
    if current:
        lines.append(f"Your actual move is `{current}`.")
    if latest:
        lines.append(f"Latest signal: \"{latest}\"")
    for note in _useful_memory_notes(knowledge)[-2:]:
        lines.append(f"I remember: {note}.")
    for avoid in (knowledge.get("avoid_rules") or [])[-2:]:
        lines.append(f"Do not do this: {avoid}.")
    for style in (knowledge.get("style_notes") or [])[-1:]:
        lines.append(f"Style pressure: {style}.")
    if not lines:
        lines.append(f"`{Path(file_path).name}` has no durable lessons yet, so this message starts the thread.")
    return lines[:5]


def _useful_memory_notes(knowledge: dict[str, Any]) -> list[str]:
    junk = {"done", "next", "and ask", "ask"}
    notes = []
    for note in knowledge.get("operator_notes") or []:
        text = str(note or "").strip()
        if not text or text.lower() in junk or len(text) < 10:
            continue
        notes.append(text)
    return notes


def _done_lines(
    file_path: str,
    record: dict[str, Any],
    operator: dict[str, Any],
    memory: dict[str, Any],
) -> list[str]:
    lines = [
        f"Stored this as message `{memory.get('message_count', 0)}` in `{memory.get('markdown') or memory.get('path') or 'logs/file_memory'}`.",
        f"Kept the router handle alive: `{(record.get('context_request') or {}).get('request_id', 'none')}`.",
    ]
    reason = _plain_snip(record.get("reason"), 180)
    if reason:
        lines.insert(0, reason)
    if record.get("event_type") == "completion":
        lines.append("Closed a lifecycle email and checked whether completion had real bound evidence.")
    elif record.get("event_type") == "codex_prompt":
        lines.append("Logged a one-per-Codex-prompt operator receipt on the local dev surface.")
    elif record.get("event_type") == "compile":
        lines.append("Registered why this file was selected for the current context pack.")
    else:
        lines.append(f"Logged `{Path(file_path).name}` as touched in the operator-intent trail.")
    return lines[:5]


def _planning_lines(
    file_path: str,
    record: dict[str, Any],
    operator: dict[str, Any],
    memory: dict[str, Any],
    failed_checks: list[dict[str, Any]],
) -> list[str]:
    knowledge = _memory_knowledge(memory)
    lines = []
    if failed_checks:
        lines.append(f"Fix `{failed_checks[0].get('key', 'unknown')}` before pretending this loop is complete.")
    context = _preferred_context(record, knowledge)
    if context:
        lines.append("Load " + ", ".join(f"`{item}`" for item in context[:4]) + " before a rewrite.")
    validation = _first_validation(record)
    if validation != "ask for context before rewrite":
        lines.append(f"Run `{validation}` after approval.")
    lines.append("Keep the next visible email to learned / done / next / ask, with the machine paperwork stored behind it.")
    lines.append(f"Let `{Path(file_path).name}` update its memory from replies before the next sim.")
    return lines[:5]


def _need_lines(
    file_path: str,
    record: dict[str, Any],
    memory: dict[str, Any],
    failed_checks: list[dict[str, Any]],
) -> list[str]:
    lines = []
    if failed_checks:
        lines.append(f"Reply `remember: {failed_checks[0].get('key', 'failed_check')} means not done yet` if that rule should persist.")
    if not (record.get("context_injection") or []):
        lines.append("Reply `use: path/to/file.py` to pin the next context pack.")
    lines.append("Reply `avoid: generic status memo` if the voice slips back into dashboard sludge.")
    lines.append("Reply `style: old friend, specific, a little unhinged, never vague` to tune the file's future mail.")
    return lines[:4]


def _actionable_comedy_line(
    file_path: str,
    beef: str,
    record: dict[str, Any],
    operator: dict[str, Any],
    memory: dict[str, Any],
    failed_checks: list[dict[str, Any]],
) -> str:
    file_name = Path(file_path).name
    if failed_checks:
        return (
            f"`{file_name}` is side-eyeing `{failed_checks[0].get('key', 'unknown')}` so hard the router felt it in JSON."
        )
    if memory.get("message_count", 0) > 2:
        return f"`{file_name}` has a mail thread now and is already acting like it owns a tiny office with strong opinions."
    if beef and beef != "unknown":
        return f"`{file_name}` is cooperating with `{Path(beef).name}`, but only because your intent said so."
    return f"`{file_name}` promises fewer clipboards and more useful notes."


def _memory_knowledge(memory: dict[str, Any]) -> dict[str, Any]:
    knowledge = memory.get("knowledge") if isinstance(memory.get("knowledge"), dict) else {}
    return knowledge


def _preferred_context(record: dict[str, Any], knowledge: dict[str, Any]) -> list[str]:
    context = [str(item) for item in (record.get("context_injection") or []) if item]
    context.extend(str(item) for item in (knowledge.get("preferred_context") or []) if item)
    out = []
    seen = set()
    for item in context:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _first_validation(record: dict[str, Any]) -> str:
    validation = record.get("validation_plan") or []
    if validation:
        return str(validation[0])
    return "ask for context before rewrite"


def _failed_check_summary(failed_checks: list[dict[str, Any]]) -> str:
    return ", ".join(f"{item.get('key', 'unknown')}={item.get('reason', '')}" for item in failed_checks[:4])


def _plain_snip(value: Any, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = re.sub(
        r"\b(?:i am|i'm|they(?:'re|re)|it(?:'s|s))?\s*not the problem\b",
        "[old defensive file-voice phrase]",
        text,
        flags=re.I,
    )
    if len(text) > limit:
        text = text[: max(0, limit - 3)].rstrip() + "..."
    return text


def _old_friend_opening(
    file_path: str,
    record: dict[str, Any],
    operator: dict[str, Any],
    failed_checks: list[dict[str, Any]],
) -> str:
    name = operator.get("operator_name") or "Nikita"
    work = operator.get("current_work") or "make the intent loop sharper than the toolchain around it"
    file_name = Path(file_path).name
    if failed_checks:
        return (
            f"Quick note from `{file_name}`: you were right to be annoyed, {name}. "
            f"The loop is doing useful work, but it is still hiding broken edges unless I drag them into the light."
        )
    if record.get("event_type") == "completion":
        return (
            f"Quick note from `{file_name}`: the loop closed, and I am writing like an old friend "
            f"because the point is your work, not my little file monologue."
        )
    return (
        f"Quick note from `{file_name}`: I saw the move. You are trying to {work}, "
        "so I brought the useful context first and saved the theatrics for after the map."
    )


def _old_friend_read(
    file_path: str,
    record: dict[str, Any],
    operator: dict[str, Any],
    failed_checks: list[dict[str, Any]],
) -> str:
    if failed_checks:
        keys = ", ".join(str(item.get("key", "unknown")) for item in failed_checks[:3])
        return f"you are close, but `{keys}` still needs receipts before I let the system call it done"
    intent = operator.get("primary_operator_intent") or "intent routing"
    return (
        f"you are steering `{intent}`; `{Path(file_path).name}` should flatter the mission by being useful, "
        "specific, and impossible to confuse with generic status spam"
    )


def _adaptive_operator_note(
    file_path: str,
    record: dict[str, Any],
    operator: dict[str, Any],
    memory: dict[str, Any],
    failed_checks: list[dict[str, Any]],
) -> str:
    current = operator.get("current_work") or "make file memory follow the way you actually think"
    latest = _operator_text_quote(operator.get("latest_operator_text") or "", 220)
    file_name = Path(file_path).name
    memory_note = ""
    if memory.get("message_count"):
        memory_note = f" This is message {memory.get('message_count')} in this thread, so this is becoming memory, not a one-off alert."
    if failed_checks:
        keys = ", ".join(str(item.get("key", "unknown")) for item in failed_checks[:3])
        return (
            f"I think the live move is this: {current}. `{file_name}` should help by remembering the conversation, "
            f"not by forcing your thought into ten little boxes. The only hard stop I see is `{keys}`.{memory_note}\n\n"
            f"Recent operator signal: {latest}"
        )
    return (
        f"I think the live move is this: {current}. `{file_name}` should adapt to that, keep the thread memory, "
        f"and only expose structure when another tool needs a handle.{memory_note}\n\n"
        f"Recent operator signal: {latest}"
    )


def _file_role_for_operator(file_path: str, record: dict[str, Any], operator: dict[str, Any]) -> str:
    event_type = record.get("event_type")
    if event_type == "submission":
        return "turn the fresh prompt into a visible, approvable work ticket"
    if event_type == "completion":
        return "close the human-to-repo loop and admit exactly what evidence is still missing"
    if event_type == "compile":
        return f"explain why `{Path(file_path).name}` belongs in the current context pack"
    if event_type == "touch":
        return f"explain why `{Path(file_path).name}` changed while preserving the operator intent trail"
    return "keep the operator intent trail coherent"


def _reasoning_operator_read(record: dict[str, Any], operator: dict[str, Any]) -> str:
    bits = []
    if operator.get("primary_operator_intent"):
        bits.append(f"intent={operator['primary_operator_intent']}")
    if operator.get("prompt_density"):
        bits.append("density=active")
    if operator.get("profile_facts"):
        bits.append("profile=loaded")
    if operator.get("file_job_summary"):
        bits.append("file_council=loaded")
    if not bits:
        bits.append("operator model is sparse; use prompt + intent key")
    return ", ".join(bits)


def _next_bounded_move(record: dict[str, Any], failed_checks: list[dict[str, Any]]) -> str:
    if failed_checks:
        first = failed_checks[0]
        return f"resolve `{first.get('key', 'unknown')}` before trusting completion"
    validation = record.get("validation_plan") or []
    if validation:
        return f"run `{validation[0]}` after approval"
    context = record.get("context_injection") or []
    if context:
        return f"load `{context[0]}` and ask for the smallest safe patch"
    return "ask for missing context before rewrite"


def _loyalty_clause(operator: dict[str, Any]) -> str:
    name = operator.get("operator_name") or "Nikita"
    intent = operator.get("primary_operator_intent") or "the operator's actual intent"
    return f"{name}'s `{intent}` beats file ego, stale model guesses, and ornamental telemetry"


def _inline_quote(value: Any, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if not text:
        return "`none captured`"
    if len(text) > limit:
        text = text[: max(0, limit - 3)].rstrip() + "..."
    return f"`{text}`"


def _operator_text_quote(value: Any, limit: int = 180) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    text = re.sub(
        r"\b(?:i am|i'm|they(?:'re|re)|it(?:'s|s))?\s*not the problem\b",
        "[old defensive file-voice phrase]",
        text,
        flags=re.I,
    )
    return _inline_quote(text, limit)


def _comedy_grievance(
    file_path: str,
    beef: str,
    record: dict[str, Any],
    failed_checks: list[dict[str, Any]],
) -> str:
    event_type = record.get("event_type")
    if failed_checks:
        keys = ", ".join(str(item.get("key", "unknown")) for item in failed_checks[:4])
        return (
            f"`{Path(file_path).name}` is not accepting a victory lap while `{keys}` "
            f"is still on the floor wearing a fake badge. `{Path(beef).name}` has been notified."
        )
    if event_type == "completion":
        return "`intent_completion` found no failed checks, which is annoying because now it has to be gracious."
    if event_type == "submission":
        return "`prompt_submission` opened the docket, sharpened the context pencils, and made approval sit in the front row."
    if event_type == "compile":
        return f"`{Path(file_path).name}` has compiled itself into testimony and is politely threatening the next stale model."
    return f"`{Path(file_path).name}` has your back: operator state first, useful context second, jokes only when they carry signal."


def _write_context_request(
    root: Path,
    config: dict[str, Any],
    record: dict[str, Any],
    event: dict[str, Any],
) -> dict[str, Any]:
    request_id = "ctx-" + hashlib.sha256(
        f"{record['id']}|{record.get('file')}|{record.get('intent_key')}".encode("utf-8")
    ).hexdigest()[:14]
    request = {
        "schema": "context_request/v1",
        "ts": record.get("ts"),
        "request_id": request_id,
        "status": "open",
        "source_email_id": record.get("id"),
        "file": record.get("file"),
        "trigger": record.get("trigger"),
        "intent_key": record.get("intent_key", ""),
        "target_state": record.get("target_state", ""),
        "deepseek_completion_job_id": record.get("deepseek_completion_job_id", ""),
        "operator_state": record.get("operator_state", {}),
        "operator_response_policy": record.get("operator_response_policy", {}),
        "required_context": record.get("context_injection", []),
        "validation_plan": record.get("validation_plan", []),
        "beef_with": record.get("beef_with", ""),
        "ten_q": record.get("ten_q", {}),
        "computed_checks": (record.get("ten_q") or {}).get("checks", []),
        "failed_checks": _failed_checks(record),
        "passed_checks": _passed_checks(record),
        "orchestrator_email_guard": record.get("orchestrator_email_guard", {}),
        "questions": _context_10q(record, event),
        "fulfillment": {
            "store_jsonl": "logs/context_request_fulfillments.jsonl",
            "store_markdown_dir": "logs/context_requests",
            "expected_record": {
                "request_id": request_id,
                "status": "fulfilled",
                "answer": "operator/codex/linkrouter supplied context",
                "files": record.get("context_injection", []),
            },
        },
    }
    req_dir = root / str(config.get("context_request_dir") or "logs/context_requests")
    req_dir.mkdir(parents=True, exist_ok=True)
    json_path = req_dir / f"{request_id}.json"
    md_path = req_dir / f"{request_id}.md"
    _write_json(json_path, request)
    md_path.write_text(_render_context_request(request), encoding="utf-8")
    _write_json(root / "logs" / "context_request_latest.json", request)
    _append_jsonl(root / "logs" / "context_requests.jsonl", request)
    return {
        "request_id": request_id,
        "status": "open",
        "ten_q": request.get("ten_q", {}),
        "computed_checks": request.get("computed_checks", []),
        "orchestrator_email_guard": request.get("orchestrator_email_guard", {}),
        "questions": request["questions"],
        "paths": {
            "json": _rel(root, json_path),
            "markdown": _rel(root, md_path),
            "latest": "logs/context_request_latest.json",
            "history": "logs/context_requests.jsonl",
            "fulfillments": "logs/context_request_fulfillments.jsonl",
        },
    }


def _context_10q(record: dict[str, Any], event: dict[str, Any]) -> list[dict[str, Any]]:
    file_path = record.get("file", "unknown")
    beef = record.get("beef_with", "unknown")
    checks = {str(item.get("key")): item for item in (record.get("ten_q") or {}).get("checks", [])}
    key_map = {
        "intent": "intent_alignment",
        "ownership": "source_target",
        "required_context": "context_available",
        "beef": "incompatibility_known",
        "incompatibility": "incompatibility_known",
        "deepseek": "deepseek_job_allowed",
        "copilot": "operator_approval",
        "validation": "validation_plan",
        "missing_context": "dirty_state_known",
        "storage": "identity_growth",
    }
    questions = [
        {"n": 1, "key": "intent", "question": f"What exact intent selected `{file_path}`?"},
        {"n": 2, "key": "ownership", "question": "Which manifest or file identity proves this file owns the change?"},
        {"n": 3, "key": "required_context", "question": "Which files must be loaded before rewrite?"},
        {"n": 4, "key": "beef", "question": f"What does `{file_path}` need from `{beef}` before it stops complaining?"},
        {"n": 5, "key": "incompatibility", "question": "Which peer proposal conflicts with this layout or import edge?"},
        {"n": 6, "key": "deepseek", "question": "What should DeepSeek draft, and what must it avoid touching?"},
        {"n": 7, "key": "copilot", "question": "What exact bounded action should Copilot execute?"},
        {"n": 8, "key": "validation", "question": "Which compile/test gates decide whether the rewrite survives?"},
        {"n": 9, "key": "missing_context", "question": "What context is still missing or stale?"},
        {"n": 10, "key": "storage", "question": "Where should the fulfilled context be stored for future prompts?"},
    ]
    for item in questions:
        mapped = key_map.get(str(item.get("key")))
        if mapped and mapped in checks:
            item["computed"] = checks[mapped]
    return questions


def _file_mail_memory_hint(root: Path, config: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    paths = _file_memory_paths(root, config, str(record.get("file") or "unknown"))
    existing = _load_json(paths["json_abs"]) or {}
    messages = existing.get("messages") if isinstance(existing.get("messages"), list) else []
    knowledge = existing.get("knowledge") if isinstance(existing.get("knowledge"), dict) else _empty_file_memory_knowledge()
    return {
        "schema": "file_mail_memory_ref/v1",
        "thread_id": _file_memory_thread_id(str(record.get("file") or "unknown")),
        "path": _rel(root, paths["json_abs"]),
        "markdown": _rel(root, paths["md_abs"]),
        "message_count": len(messages) + 1,
        "knowledge": knowledge,
        "mode": "email_thread_is_memory",
    }


def _write_file_mail_memory(
    root: Path,
    config: dict[str, Any],
    record: dict[str, Any],
    body: str,
    paths: dict[str, str],
) -> dict[str, Any]:
    root = Path(root)
    file_path = str(record.get("file") or "unknown")
    mem_paths = _file_memory_paths(root, config, file_path)
    memory = _load_json(mem_paths["json_abs"])
    if not isinstance(memory, dict) or memory.get("schema") != "file_mail_memory/v1":
        memory = {
            "schema": "file_mail_memory/v1",
            "thread_id": _file_memory_thread_id(file_path),
            "file": file_path,
            "created_at": record.get("ts"),
            "messages": [],
            "knowledge": _empty_file_memory_knowledge(),
        }
    event = _file_memory_message(record, body, paths, direction="outbound")
    memory.setdefault("messages", []).append(event)
    memory["updated_at"] = record.get("ts")
    memory["knowledge"] = _merge_file_memory_knowledge(memory.get("knowledge"), event)
    mem_paths["json_abs"].parent.mkdir(parents=True, exist_ok=True)
    _write_json(mem_paths["json_abs"], memory)
    mem_paths["md_abs"].write_text(_render_file_memory(memory), encoding="utf-8")
    _write_json(root / "logs" / "file_memory_latest.json", memory)
    _append_jsonl(root / "logs" / "file_memory_messages.jsonl", event)
    _write_file_memory_index(root, config)
    return {
        "schema": "file_mail_memory_ref/v1",
        "thread_id": memory.get("thread_id"),
        "path": _rel(root, mem_paths["json_abs"]),
        "markdown": _rel(root, mem_paths["md_abs"]),
        "message_count": len(memory.get("messages") or []),
        "knowledge": memory.get("knowledge", {}),
        "mode": "email_thread_is_memory",
    }


def ingest_file_mail_reply(
    root: Path,
    file_path: str,
    message: str,
    subject: str = "",
    source: str = "operator_email",
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(root)
    config = merge_file_email_config(config or load_file_email_config(root))
    now = datetime.now(timezone.utc).isoformat()
    record = {
        "schema": "file_mail_reply/v1",
        "ts": now,
        "id": "file-reply:" + hashlib.sha256(f"{file_path}|{subject}|{message}|{now}".encode("utf-8")).hexdigest()[:16],
        "direction": "inbound",
        "source": source,
        "file": file_path or "unknown",
        "subject": subject or f"reply to {file_path}",
        "body": str(message or ""),
        "commands": _parse_mail_memory_commands(message),
    }
    mem_paths = _file_memory_paths(root, config, record["file"])
    memory = _load_json(mem_paths["json_abs"])
    if not isinstance(memory, dict) or memory.get("schema") != "file_mail_memory/v1":
        memory = {
            "schema": "file_mail_memory/v1",
            "thread_id": _file_memory_thread_id(record["file"]),
            "file": record["file"],
            "created_at": now,
            "messages": [],
            "knowledge": _empty_file_memory_knowledge(),
        }
    event = {
        "schema": "file_mail_message/v1",
        "ts": now,
        "direction": "inbound",
        "source": source,
        "message_id": record["id"],
        "file": record["file"],
        "subject": record["subject"],
        "body": record["body"],
        "commands": record["commands"],
        "tags": ["operator_reply", "mail_memory"],
    }
    memory.setdefault("messages", []).append(event)
    memory["updated_at"] = now
    memory["knowledge"] = _merge_file_memory_knowledge(memory.get("knowledge"), event)
    memory["knowledge"] = _apply_mail_memory_commands(memory["knowledge"], record["commands"])
    _write_json(mem_paths["json_abs"], memory)
    mem_paths["md_abs"].write_text(_render_file_memory(memory), encoding="utf-8")
    _write_json(root / "logs" / "file_memory_latest.json", memory)
    _append_jsonl(root / "logs" / "file_memory_messages.jsonl", event)
    _append_jsonl(root / "logs" / "file_mail_replies.jsonl", record)
    _write_file_memory_index(root, config)
    record["memory"] = {
        "thread_id": memory.get("thread_id"),
        "path": _rel(root, mem_paths["json_abs"]),
        "markdown": _rel(root, mem_paths["md_abs"]),
        "message_count": len(memory.get("messages") or []),
    }
    return record


def _file_memory_paths(root: Path, config: dict[str, Any], file_path: str) -> dict[str, Path]:
    memory_dir = root / str(config.get("memory_dir") or DEFAULT_CONFIG["memory_dir"])
    safe = _safe_filename(str(file_path).replace("\\", "__").replace("/", "__"))
    return {"json_abs": memory_dir / f"{safe}.json", "md_abs": memory_dir / f"{safe}.md"}


def _file_memory_thread_id(file_path: str) -> str:
    return "fmt-" + hashlib.sha256(str(file_path or "unknown").replace("\\", "/").encode("utf-8")).hexdigest()[:14]


def _file_memory_message(
    record: dict[str, Any],
    body: str,
    paths: dict[str, str],
    direction: str,
) -> dict[str, Any]:
    operator = record.get("operator_state") if isinstance(record.get("operator_state"), dict) else {}
    return {
        "schema": "file_mail_message/v1",
        "ts": record.get("ts"),
        "direction": direction,
        "message_id": record.get("id"),
        "file": record.get("file"),
        "subject": record.get("subject"),
        "body": body,
        "body_preview": re.sub(r"\s+", " ", str(body or "")).strip()[:700],
        "paths": paths,
        "event_type": record.get("event_type"),
        "trigger": record.get("trigger"),
        "intent_key": record.get("intent_key", ""),
        "operator_intent": operator.get("primary_operator_intent", ""),
        "current_work": operator.get("current_work", ""),
        "latest_operator_text": operator.get("latest_operator_text", ""),
        "context_request_id": (record.get("context_request") or {}).get("request_id", ""),
        "context_files": record.get("context_injection", []),
        "validation_plan": record.get("validation_plan", []),
        "failed_checks": _failed_checks(record),
        "relationship_tension": record.get("beef_with", ""),
        "tags": _file_memory_tags(record),
    }


def _empty_file_memory_knowledge() -> dict[str, Any]:
    return {
        "operator_intents": {},
        "intent_keys": {},
        "neighbors": {},
        "failed_checks": {},
        "decisions": {},
        "operator_notes": [],
        "preferred_context": [],
        "avoid_rules": [],
        "style_notes": [
            "visible mail should adapt to operator cognitive style",
            "machine structure belongs under the hood",
        ],
        "last_current_work": "",
        "last_operator_signal": "",
    }


def _merge_file_memory_knowledge(knowledge: Any, event: dict[str, Any]) -> dict[str, Any]:
    out = knowledge if isinstance(knowledge, dict) else _empty_file_memory_knowledge()
    for key, default in _empty_file_memory_knowledge().items():
        out.setdefault(key, default.copy() if isinstance(default, (dict, list)) else default)
    _bump(out["operator_intents"], event.get("operator_intent"))
    _bump(out["intent_keys"], event.get("intent_key"))
    _bump(out["decisions"], event.get("event_type"))
    _bump(out["neighbors"], event.get("relationship_tension"))
    for item in event.get("context_files") or []:
        _bump(out["neighbors"], item)
    for item in event.get("failed_checks") or []:
        if isinstance(item, dict):
            _bump(out["failed_checks"], item.get("key"))
    if event.get("current_work"):
        out["last_current_work"] = event.get("current_work")
    if event.get("latest_operator_text"):
        out["last_operator_signal"] = str(event.get("latest_operator_text"))[:500]
    return out


def _apply_mail_memory_commands(knowledge: dict[str, Any], commands: dict[str, list[str]]) -> dict[str, Any]:
    for note in commands.get("remember", []):
        _append_unique(knowledge.setdefault("operator_notes", []), note)
    for item in commands.get("use", []):
        _append_unique(knowledge.setdefault("preferred_context", []), item)
    for item in commands.get("avoid", []):
        _append_unique(knowledge.setdefault("avoid_rules", []), item)
    for item in commands.get("style", []):
        _append_unique(knowledge.setdefault("style_notes", []), item)
    return knowledge


def _parse_mail_memory_commands(message: str) -> dict[str, list[str]]:
    commands = {"remember": [], "use": [], "avoid": [], "style": [], "note": []}
    for raw in str(message or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        match = re.match(r"^(remember|use|avoid|style)\s*:\s*(.+)$", line, re.I)
        if match:
            key = match.group(1).lower()
            values = _split_mail_command_values(match.group(2)) if key == "use" else [match.group(2).strip()]
            commands[key].extend(values)
        else:
            commands["note"].append(line)
    return {key: value for key, value in commands.items() if value}


def _split_mail_command_values(value: str) -> list[str]:
    parts = [part.strip() for part in re.split(r",|\s+\+\s+|\s+;\s+", value) if part.strip()]
    return parts or [value.strip()]


def _file_memory_tags(record: dict[str, Any]) -> list[str]:
    operator = record.get("operator_state") if isinstance(record.get("operator_state"), dict) else {}
    tags = ["file_mail", str(record.get("event_type") or "event")]
    if operator.get("primary_operator_intent"):
        tags.append(str(operator.get("primary_operator_intent")))
    if _failed_checks(record):
        tags.append("failed_checks")
    if record.get("intent_key"):
        tags.append("intent_keyed")
    return _dedupe_list(tags)


def _render_file_memory(memory: dict[str, Any]) -> str:
    knowledge = memory.get("knowledge") if isinstance(memory.get("knowledge"), dict) else {}
    lines = [
        "# File Mail Memory",
        "",
        f"- file: `{memory.get('file')}`",
        f"- thread_id: `{memory.get('thread_id')}`",
        f"- updated_at: `{memory.get('updated_at', memory.get('created_at', ''))}`",
        f"- messages: `{len(memory.get('messages') or [])}`",
        "",
        "## What This File Knows",
        "",
        f"- current work: {knowledge.get('last_current_work') or 'unknown'}",
        f"- latest operator signal: {_inline_quote(knowledge.get('last_operator_signal') or '', 260)}",
        f"- preferred context: `{', '.join((knowledge.get('preferred_context') or [])[:12]) or 'none'}`",
        f"- avoid: `{', '.join((knowledge.get('avoid_rules') or [])[:12]) or 'none'}`",
        f"- style: `{', '.join((knowledge.get('style_notes') or [])[:8]) or 'adaptive mail'}`",
        "",
        "## Counts",
        "",
        f"- operator intents: `{_top_counts(knowledge.get('operator_intents'))}`",
        f"- intent keys: `{_top_counts(knowledge.get('intent_keys'))}`",
        f"- neighbors: `{_top_counts(knowledge.get('neighbors'))}`",
        f"- failed checks: `{_top_counts(knowledge.get('failed_checks'))}`",
        "",
        "## Notes From Replies",
        "",
    ]
    notes = knowledge.get("operator_notes") or []
    lines.extend(f"- {note}" for note in notes[-12:]) if notes else lines.append("- none yet")
    lines.extend(["", "## Recent Messages", ""])
    for msg in (memory.get("messages") or [])[-8:]:
        lines.extend([
            f"### {msg.get('ts')} - {msg.get('direction')} - {msg.get('subject', '')}",
            "",
            str(msg.get("body_preview") or msg.get("body") or "")[:900],
            "",
        ])
    return "\n".join(lines)


def _write_file_memory_index(root: Path, config: dict[str, Any]) -> None:
    memory_dir = root / str(config.get("memory_dir") or DEFAULT_CONFIG["memory_dir"])
    rows = []
    for path in sorted(memory_dir.glob("*.json"))[:5000]:
        data = _load_json(path)
        if not isinstance(data, dict):
            continue
        rows.append({
            "file": data.get("file"),
            "thread_id": data.get("thread_id"),
            "updated_at": data.get("updated_at"),
            "messages": len(data.get("messages") or []),
            "path": _rel(root, path),
            "markdown": _rel(root, path.with_suffix(".md")),
        })
    _write_json(root / "logs" / "file_memory_index.json", {
        "schema": "file_memory_index/v1",
        "ts": datetime.now(timezone.utc).isoformat(),
        "count": len(rows),
        "files": rows,
    })


def _bump(counter: dict[str, int], key: Any) -> None:
    text = str(key or "").strip()
    if text:
        counter[text] = int(counter.get(text, 0)) + 1


def _append_unique(values: list[str], value: str, limit: int = 80) -> None:
    text = str(value or "").strip()
    if text and text not in values:
        values.append(text)
    del values[:-limit]


def _top_counts(counts: Any, limit: int = 8) -> str:
    if not isinstance(counts, dict) or not counts:
        return "none"
    return ", ".join(f"{key}:{value}" for key, value in sorted(counts.items(), key=lambda item: (-int(item[1]), item[0]))[:limit])


def _dedupe_list(values: list[str]) -> list[str]:
    out = []
    seen = set()
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        out.append(value)
    return out


def _operator_state_snapshot(root: Path, event: dict[str, Any]) -> dict[str, Any]:
    logs = Path(root) / "logs"
    semantic_latest = _load_json(logs / "semantic_profile_latest.json") or {}
    semantic_profile = _load_json(logs / "semantic_profile.json") or {}
    ai_fingerprint = _load_json(logs / "ai_fingerprint.json") or {}
    operator_current = _load_json(logs / "operator_state_current.json") or {}
    intent_latest = _load_json(logs / "intent_key_latest.json") or {}
    prompt_latest = _latest_jsonl(logs / "prompt_journal.jsonl")
    brain_latest = _load_json(logs / "prompt_brain_latest.json") or {}
    council_latest = _load_json(logs / "file_job_council_latest.json") or {}
    facts = _profile_facts(semantic_profile, ai_fingerprint)
    latest_text = _latest_operator_text(semantic_latest, prompt_latest, brain_latest, event)
    semantic_intents = semantic_latest.get("semantic_intents") if isinstance(semantic_latest.get("semantic_intents"), list) else []
    primary = str(semantic_latest.get("semantic_intent") or "")
    if not primary or primary == "unknown":
        primary = _infer_operator_intent(latest_text, semantic_intents, event)
    return {
        "schema": "operator_state_email/v1",
        "operator_name": _operator_name_from_facts(facts),
        "primary_operator_intent": primary,
        "semantic_intents": semantic_intents,
        "operator_intent_key": event.get("intent_key") or intent_latest.get("intent_key") or brain_latest.get("intent_key") or "",
        "current_work": _current_work_summary(latest_text, primary, event, council_latest),
        "latest_operator_text": latest_text,
        "state_source": _state_source(semantic_latest, operator_current, prompt_latest),
        "profile_facts": facts,
        "prompt_density": operator_current.get("prompt_density") if isinstance(operator_current, dict) else {},
        "file_job_summary": council_latest.get("comedy_summary", "") if isinstance(council_latest, dict) else "",
        "numeric_encoding": semantic_latest.get("numeric_encoding", {}) if isinstance(semantic_latest, dict) else {},
    }


def _profile_facts(semantic_profile: dict[str, Any], ai_fingerprint: dict[str, Any]) -> dict[str, Any]:
    semantic_facts = semantic_profile.get("facts") if isinstance(semantic_profile.get("facts"), dict) else {}
    ai_facts = ai_fingerprint.get("facts") if isinstance(ai_fingerprint.get("facts"), dict) else {}
    merged = dict(ai_facts)
    merged.update(semantic_facts)
    return merged


def _operator_name_from_facts(facts: dict[str, Any]) -> str:
    name = facts.get("name") if isinstance(facts.get("name"), dict) else {}
    value = str(name.get("value") or "").strip()
    return value or "Nikita"


def _latest_operator_text(
    semantic_latest: dict[str, Any],
    prompt_latest: dict[str, Any],
    brain_latest: dict[str, Any],
    event: dict[str, Any],
) -> str:
    for source in (semantic_latest, prompt_latest, brain_latest, event):
        if not isinstance(source, dict):
            continue
        for key in ("text", "msg", "prompt", "final_text", "reason"):
            value = str(source.get(key) or "").strip()
            if value:
                return value
    return ""


def _infer_operator_intent(text: str, semantic_intents: list[str], event: dict[str, Any]) -> str:
    lower = str(text or "").lower()
    if any(bit in lower for bit in ("actionable", "what its learned", "what it learned", "what got done", "planning", "personalization", "written by chat gpt")):
        return "file_voice_design"
    if ("email" in lower or "mail" in lower) and ("memory" in lower or "knowledge" in lower or "messages" in lower):
        return "file_memory_management"
    if "operatorstate" in lower or ("operator" in lower and "state" in lower):
        return "operator_state_modeling"
    if "old friend" in lower or "sycophantic" in lower or ("email" in lower and "feel" in lower):
        return "file_voice_design"
    if "email" in lower or "mail" in lower:
        return "telemetry_email"
    if "reasoning" in lower:
        return "reasoning_depth"
    for intent in semantic_intents:
        if intent and intent != "unknown":
            return intent
    if event.get("event_type") in {"submission", "completion"}:
        return "prompt_lifecycle"
    return "unknown"


def _current_work_summary(
    latest_text: str,
    primary: str,
    event: dict[str, Any],
    council_latest: dict[str, Any],
) -> str:
    lower = str(latest_text or "").lower()
    if any(bit in lower for bit in ("actionable", "what its learned", "what it learned", "what got done", "planning", "personalization", "written by chat gpt")):
        return "make visible file mail show what it learned, what got done, what comes next, and what it needs"
    if ("email" in lower or "mail" in lower) and ("memory" in lower or "knowledge" in lower or "messages" in lower):
        return "manage files through email threads and store file knowledge as long-term memory"
    if "manage my files" in lower:
        return "manage files through conversational mail instead of forcing rigid prompt boxes"
    if "old friend" in lower or "sycophantic" in lower:
        return "make file emails read like operator-aware notes from a trusted collaborator"
    if "operatorstate" in lower or ("operator" in lower and "state" in lower):
        return "center file telemetry on the live operator model instead of generic file status"
    if council_latest.get("comedy_summary"):
        return str(council_latest.get("comedy_summary"))
    if primary == "telemetry_email":
        return "turn prompt telemetry into useful local mail and context requests"
    if event.get("intent_key"):
        return f"advance `{event.get('intent_key')}`"
    return "keep the intent loop visible and operator-aligned"


def _state_source(
    semantic_latest: dict[str, Any],
    operator_current: dict[str, Any],
    prompt_latest: dict[str, Any],
) -> str:
    sources = []
    if semantic_latest:
        sources.append("semantic_profile_latest")
    if operator_current:
        sources.append("operator_state_current")
    if prompt_latest:
        sources.append("prompt_journal")
    return "+".join(sources) or "event_only"


def _render_context_request(request: dict[str, Any]) -> str:
    lines = [
        "# 10Q INT Context Request",
        "",
        f"- request_id: `{request.get('request_id')}`",
        f"- status: `{request.get('status')}`",
        f"- file: `{request.get('file')}`",
        f"- intent_key: `{request.get('intent_key')}`",
        f"- beef_with: `{request.get('beef_with')}`",
        f"- 10Q consensus: `{_ten_q_line(request)}`",
        f"- orchestrator_email_guard: `{_guard_line(request)}`",
        "",
        "## Questions",
        "",
    ]
    for item in request.get("questions", []):
        computed = item.get("computed") or {}
        suffix = ""
        if computed:
            suffix = f" `{ 'PASS' if computed.get('passed') else 'FAIL' }` {computed.get('reason')}"
        lines.append(f"{item.get('n')}. **{item.get('key')}** - {item.get('question')}{suffix}")
    lines.extend([
        "",
        "## Required Context",
        "",
    ])
    required = request.get("required_context") or []
    lines.extend(f"- `{item}`" for item in required[:12]) if required else lines.append("- none")
    lines.extend([
        "",
        "## Computed Checks",
        "",
    ])
    checks = request.get("computed_checks") or []
    if checks:
        for item in checks[:10]:
            mark = "PASS" if item.get("passed") else "FAIL"
            lines.append(f"- `{mark}` `{item.get('key')}` - {item.get('reason')}")
    else:
        lines.append("- no computed 10Q checks attached")
    failed = request.get("failed_checks") or [item for item in checks if not item.get("passed")]
    lines.extend([
        "",
        "## Failed Checks",
        "",
    ])
    if failed:
        for item in failed[:10]:
            lines.append(_format_check_line(item, "FAIL"))
    else:
        lines.append("- none")
    lines.extend([
        "",
        "## Fulfillment Storage",
        "",
        "- JSONL: `logs/context_request_fulfillments.jsonl`",
        "- Per-request markdown/json: `logs/context_requests/`",
        "",
    ])
    return "\n".join(lines)


def fulfill_context_request(
    root: Path,
    request_id: str,
    answer: str,
    files: list[str] | None = None,
    source: str = "operator",
) -> dict[str, Any]:
    root = Path(root)
    record = {
        "schema": "context_request_fulfillment/v1",
        "ts": datetime.now(timezone.utc).isoformat(),
        "request_id": request_id,
        "status": "fulfilled",
        "source": source,
        "answer": answer,
        "files": files or [],
    }
    _append_jsonl(root / "logs" / "context_request_fulfillments.jsonl", record)
    _write_json(root / "logs" / "context_request_fulfillment_latest.json", record)
    return record


def _ten_q_line(record: dict[str, Any]) -> str:
    ten_q = record.get("ten_q") or {}
    if not ten_q:
        return "unscored"
    status = "PASS" if ten_q.get("passed") else "FAIL"
    return f"{status} {ten_q.get('score', 0)}/{ten_q.get('max_score', 10)} - {ten_q.get('reason', '')}"


def _guard_line(record: dict[str, Any]) -> str:
    guard = record.get("orchestrator_email_guard") or {}
    if not guard:
        return "local_only - no orchestrator guard attached"
    return f"{guard.get('decision', 'unknown')} - {guard.get('reason', '')}"


def _delivery_guard(record: dict[str, Any]) -> dict[str, Any]:
    ten_q = record.get("ten_q") or {}
    guard = record.get("orchestrator_email_guard") or {}
    if record.get("event_type") == "learning_digest" and (guard.get("decision") == "allow_email" or guard.get("aligned")):
        return {
            "schema": "email_delivery_guard/v1",
            "aligned": True,
            "decision": "allow_email",
            "reason": guard.get("reason", "slow self-fix learning digest is operator-visible"),
        }
    if record.get("file") == "orchestrator/prompt_monitor" and record.get("trigger") in {"log_prompt", "pre_prompt", "os_hook_auto", "composition", "composition_submit"}:
        return {
            "schema": "email_delivery_guard/v1",
            "aligned": True,
            "decision": "allow_email",
            "reason": "file sim prompt monitor receipt is operator-visible even without a safe rewrite candidate",
        }
    if not ten_q or not guard:
        return {
            "schema": "email_delivery_guard/v1",
            "aligned": False,
            "decision": "local_only",
            "reason": "no consensus 10Q guard attached",
        }
    if not ten_q.get("passed"):
        return {
            "schema": "email_delivery_guard/v1",
            "aligned": False,
            "decision": "local_only",
            "reason": f"10Q failed: {ten_q.get('reason', 'unknown')}",
        }
    if guard.get("decision") != "allow_email" or not guard.get("aligned"):
        return {
            "schema": "email_delivery_guard/v1",
            "aligned": False,
            "decision": guard.get("decision", "local_only"),
            "reason": guard.get("reason", "orchestrator did not allow email"),
        }
    return {
        "schema": "email_delivery_guard/v1",
        "aligned": True,
        "decision": "allow_email",
        "reason": guard.get("reason", "10Q consensus passed"),
    }


def _deliver_resend(root: Path, config: dict[str, Any], record: dict[str, Any], body: str) -> dict[str, Any]:
    _load_local_email_env(root)
    mode = os.environ.get("FILE_EMAIL_DELIVERY") or str(config.get("delivery_mode") or "resend_dry_run")
    payload = _resend_payload(config, record, body)
    guard = _delivery_guard(record)
    payload_record = {
        "schema": "resend_payload/v1",
        "ts": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "email_id": record.get("id"),
        "api_url": config.get("resend_api_url"),
        "api_key_present": bool(os.environ.get("RESEND_API_KEY")),
        "orchestrator_guard": guard,
        "payload": payload,
    }
    _write_json(root / "logs" / "resend_payload_latest.json", payload_record)
    _append_jsonl(root / "logs" / "resend_payloads.jsonl", payload_record)
    if mode != "resend":
        email_delivery_status(root, config)
        return {
            "status": "dry_run",
            "mode": mode,
            "would_send": bool(guard.get("aligned")),
            "orchestrator_guard": guard,
            "payload_path": "logs/resend_payload_latest.json",
        }
    if not guard.get("aligned"):
        email_delivery_status(root, config)
        return {
            "status": "blocked_by_orchestrator",
            "mode": mode,
            "reason": guard.get("reason", "consensus guard failed"),
            "orchestrator_guard": guard,
            "payload_path": "logs/resend_payload_latest.json",
        }
    api_key = os.environ.get("RESEND_API_KEY", "")
    if not api_key:
        email_delivery_status(root, config)
        return {
            "status": "not_sent",
            "mode": mode,
            "reason": "missing_RESEND_API_KEY",
            "payload_path": "logs/resend_payload_latest.json",
        }
    try:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            str(config.get("resend_api_url") or DEFAULT_CONFIG["resend_api_url"]),
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": os.environ.get("RESEND_USER_AGENT") or str(config.get("resend_user_agent") or DEFAULT_CONFIG["resend_user_agent"]),
                "Idempotency-Key": str(record.get("id", ""))[:64],
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8", errors="replace")
        parsed = json.loads(text) if text.strip().startswith("{") else {"raw": text}
        email_delivery_status(root, config)
        return {"status": "sent", "mode": mode, "response": parsed}
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode("utf-8", errors="replace")
        email_delivery_status(root, config)
        return {"status": "error", "mode": mode, "http_status": exc.code, "error": body_text[:1000]}
    except Exception as exc:
        email_delivery_status(root, config)
        return {"status": "error", "mode": mode, "error": str(exc)}


def _load_local_email_env(root: Path) -> dict[str, bool]:
    loaded: dict[str, bool] = {}
    for path in [Path(root) / ".env", Path(root) / "logs" / "file_email.env"]:
        if not path.exists():
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for line in lines:
            raw = line.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            key, value = raw.split("=", 1)
            key = key.strip()
            if key not in {"RESEND_API_KEY", "RESEND_FROM", "FILE_EMAIL_DELIVERY", "RESEND_USER_AGENT"}:
                continue
            if key not in os.environ:
                os.environ[key] = value.strip().strip("'\"")
                loaded[key] = True
    return loaded


def _resend_payload(config: dict[str, Any], record: dict[str, Any], body: str) -> dict[str, Any]:
    text = body
    return {
        "from": os.environ.get("RESEND_FROM") or str(config.get("resend_from") or DEFAULT_CONFIG["resend_from"]),
        "to": [record.get("to") or DEFAULT_CONFIG["recipient"]],
        "subject": record.get("subject") or "File comedy dispatch",
        "text": text,
        "html": "<pre style=\"white-space:pre-wrap;font-family:monospace\">" + html.escape(text) + "</pre>",
        "headers": {
            "X-File-Email-Id": str(record.get("id", "")),
            "X-Context-Request-Id": str((record.get("context_request") or {}).get("request_id", "")),
            "X-Intent-Key": str(record.get("intent_key", ""))[:240],
            "X-10Q-Score": str((record.get("ten_q") or {}).get("score", "")),
            "X-10Q-Passed": str((record.get("ten_q") or {}).get("passed", "")),
            "X-Orchestrator-Email-Guard": str((record.get("orchestrator_email_guard") or {}).get("decision", "")),
        },
        "tags": [
            {"name": "trigger", "value": _safe_tag(record.get("trigger", "manual"))},
            {"name": "event_type", "value": _safe_tag(record.get("event_type", "touch"))},
        ],
    }


def _write_outbox(
    root: Path,
    config: dict[str, Any],
    record: dict[str, Any],
    body: str,
    now: datetime,
) -> dict[str, str]:
    outbox = root / str(config.get("outbox_dir") or "logs/file_email_outbox")
    outbox.mkdir(parents=True, exist_ok=True)
    safe = _safe_filename(f"{now.strftime('%Y%m%dT%H%M%S')}_{Path(record['file']).stem}_{record['event_type']}")
    paths: dict[str, str] = {}
    if config.get("write_markdown", True):
        md_path = outbox / f"{safe}.md"
        md_path.write_text(body, encoding="utf-8")
        (root / "logs" / "file_email_latest.md").write_text(body, encoding="utf-8")
        paths["markdown"] = _rel(root, md_path)
    if config.get("write_eml", True):
        msg = EmailMessage()
        msg["From"] = record["from"]
        msg["To"] = record["to"]
        msg["Subject"] = record["subject"]
        msg["Date"] = format_datetime(now)
        msg["Message-ID"] = make_msgid(domain=str(config.get("sender_domain", "files.local")))
        msg.set_content(body, subtype="plain", charset="utf-8")
        eml_path = outbox / f"{safe}.eml"
        eml_path.write_bytes(bytes(msg))
        paths["eml"] = _rel(root, eml_path)
    return paths


def _choose_beef(proposal: dict[str, Any], proposals: list[dict[str, Any]]) -> str:
    refs = proposal.get("context_injection") if isinstance(proposal.get("context_injection"), list) else []
    self_path = str(proposal.get("path") or "")
    for item in refs:
        item_s = str(item)
        if item_s and item_s != self_path and not item_s.lower().endswith("manifest.md"):
            return item_s
    for other in proposals:
        other_path = str(other.get("path") or "")
        if other_path and other_path != self_path:
            return other_path
    return "unresolved shared state"


def _touch_beef(file_path: str, prompt: str) -> str:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_]+", str(prompt).lower())
    if "context" in words:
        return "context_selection"
    if "intent" in words:
        return "intent_key_latest"
    if "test" in words:
        return "the test suite"
    parent = Path(file_path or "").parent.as_posix()
    return parent or "the repo root"


def _subject(file_path: str, beef_with: str, event: dict[str, Any]) -> str:
    stem = Path(file_path).stem or "unknown file"
    enemy = Path(beef_with).stem or str(beef_with)
    if event.get("event_type") == "submission":
        verb = "sent an old-friend note about"
    elif event.get("event_type") == "completion":
        verb = "closed the loop and briefed"
    elif event.get("event_type") == "codex_prompt":
        verb = "received a Codex prompt for"
    else:
        verb = "sent context for" if event.get("event_type") == "compile" else "was touched and updated"
    return f"{stem} {verb} {enemy}"


def _event_voice(event_type: Any) -> str:
    if event_type == "compile":
        return "compiled"
    if event_type == "submission":
        return "submitted"
    if event_type == "completion":
        return "completed"
    if event_type == "codex_prompt":
        return "received"
    return "touched"


def _closing_argument(file_path: str, beef: str, record: dict[str, Any]) -> str:
    if record.get("event_type") == "compile":
        return f"`{Path(file_path).name}` will accept a rewrite when `{Path(beef).name}` is in the room and validation signs the minutes."
    if record.get("event_type") == "submission":
        return "`prompt_submission` opened the case file. The files may now testify, but nobody gets overwritten without approval."
    if record.get("event_type") == "completion":
        failed = _failed_checks(record)
        if failed:
            keys = ", ".join(str(item.get("key", "unknown")) for item in failed[:3])
            return f"`intent_completion` filed the receipt, then refused to smile because `{keys}` still failed."
        return "`intent_completion` closed the loop, stamped the receipt, and left a training crumb for future routing."
    if record.get("event_type") == "codex_prompt":
        return "`codex_prompt` heard the operator directly and filed a dev-surface receipt before any web-chat lane could touch it."
    return f"`{Path(file_path).name}` changed in the operator-state lane and will keep future mail centered on the actual work."


def _enabled(config: dict[str, Any], trigger: str) -> bool:
    return bool(config.get("enabled", True)) and trigger in set(config.get("triggers") or [])


def _safe_mailbox(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_.-]+", ".", value.lower()).strip(".")
    return clean[:48] or "file"


def _safe_filename(value: str) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_.-]+", "_", value).strip("_")
    return clean[:120] or "file_email"


def _safe_tag(value: Any) -> str:
    clean = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(value).lower()).strip("_")
    return clean[:60] or "file"


def _rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def _latest_jsonl(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        return {}
    for line in reversed(lines):
        try:
            row = json.loads(line)
        except Exception:
            continue
        if isinstance(row, dict):
            return row
    return {}


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
