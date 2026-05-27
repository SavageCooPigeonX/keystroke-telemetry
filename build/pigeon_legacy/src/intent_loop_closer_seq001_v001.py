"""Durable human -> Copilot -> repo-plugin intent loop receipts.

The prompt brain and file simulator already compile intent and propose work.
This module adds the missing receipt layer: every prompt can open a loop ticket,
later AI responses and file edits bind back to that ticket, and a verified close
turns the loop into training data.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LATEST_PATH = "logs/intent_loop_latest.json"
HISTORY_PATH = "logs/intent_loop_history.jsonl"
BINDINGS_PATH = "logs/intent_loop_bindings.jsonl"
COMPLETIONS_PATH = "logs/intent_loop_completions.jsonl"
REGISTRY_PATH = "logs/intent_loop_registry.json"
TRAINING_CANDIDATES_PATH = "logs/intent_loop_training_candidates.jsonl"
OPEN_STATUSES = {
    "awaiting_operator_approval",
    "waiting_for_copilot_execution",
    "response_observed",
    "execution_observed",
    "monitoring",
    "monitoring_no_rewrite_proposal",
    "blocked_file_sim_error",
}
CLOSED_STATUSES = {"verified", "done", "resolved", "rejected", "abandoned"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _digest(*parts: Any) -> str:
    seed = "|".join(str(part or "") for part in parts)
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:16]


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _proposal_rows(file_sim: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for proposal in _as_list(file_sim.get("proposals"))[:12]:
        ten_q = proposal.get("ten_q") if isinstance(proposal.get("ten_q"), dict) else {}
        guard = proposal.get("orchestrator_email_guard") if isinstance(proposal.get("orchestrator_email_guard"), dict) else {}
        rows.append({
            "file": proposal.get("path"),
            "decision": proposal.get("decision"),
            "proposed_fix": proposal.get("proposed_fix"),
            "interlink_score": proposal.get("interlink_score"),
            "ten_q_score": ten_q.get("score"),
            "ten_q_passed": ten_q.get("passed"),
            "guard": guard.get("decision"),
            "approval_gate": proposal.get("approval_gate"),
            "deepseek_job_id": proposal.get("deepseek_completion_job_id"),
            "validation_plan": _as_list(proposal.get("validation_plan"))[:6],
        })
    return rows


def _focus_files(context_selection: dict[str, Any] | None, file_sim: dict[str, Any]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for proposal in _proposal_rows(file_sim):
        name = str(proposal.get("file") or "").strip()
        if name and name not in seen:
            seen.add(name)
            out.append(name)
    context = context_selection if isinstance(context_selection, dict) else {}
    for item in _as_list(context.get("files")):
        name = item.get("name") if isinstance(item, dict) else item
        name = str(name or "").strip()
        if name and name not in seen:
            seen.add(name)
            out.append(name)
    return out[:24]


def _intent_key(root: Path, prompt: str, file_sim: dict[str, Any], prompt_brain: dict[str, Any] | None) -> str:
    sim_intent = file_sim.get("intent") if isinstance(file_sim.get("intent"), dict) else {}
    if sim_intent.get("intent_key"):
        return str(sim_intent.get("intent_key"))
    brain = prompt_brain if isinstance(prompt_brain, dict) else {}
    if brain.get("intent_key"):
        return str(brain.get("intent_key"))
    latest = _load_json(root / "logs" / "intent_key_latest.json")
    if isinstance(latest, dict) and latest.get("intent_key"):
        return str(latest.get("intent_key"))
    return f"root:route:{_digest(prompt)[:8]}:minor"


def _loop_status(file_sim: dict[str, Any]) -> str:
    if file_sim.get("status") == "error":
        return "blocked_file_sim_error"
    proposals = _as_list(file_sim.get("proposals"))
    if not proposals:
        return "monitoring_no_rewrite_proposal"
    orchestrator = file_sim.get("orchestrator") if isinstance(file_sim.get("orchestrator"), dict) else {}
    approval_required = bool(orchestrator.get("approval_required", True))
    auto_write = bool(orchestrator.get("auto_write_allowed", False))
    if approval_required or any(p.get("approval_gate") == "operator_required" for p in proposals if isinstance(p, dict)):
        return "awaiting_operator_approval"
    if auto_write:
        return "waiting_for_copilot_execution"
    return "monitoring"


def _load_registry(root: Path) -> dict[str, Any]:
    data = _load_json(root / REGISTRY_PATH)
    if isinstance(data, dict):
        data.setdefault("open", [])
        data.setdefault("closed", [])
        return data
    return {"schema": "intent_loop_registry/v1", "open": [], "closed": []}


def _replace_loop(rows: list[dict[str, Any]], loop: dict[str, Any]) -> list[dict[str, Any]]:
    loop_id = loop.get("loop_id")
    filtered = [row for row in rows if row.get("loop_id") != loop_id]
    filtered.append(loop)
    return filtered[-100:]


def _write_loop(root: Path, loop: dict[str, Any], event: str) -> dict[str, Any]:
    loop = dict(loop)
    loop["updated_ts"] = _utc_now()
    _write_json(root / LATEST_PATH, loop)
    _append_jsonl(root / HISTORY_PATH, {"event": event, **loop})

    registry = _load_registry(root)
    registry["updated_ts"] = loop["updated_ts"]
    registry["open"] = [row for row in registry.get("open", []) if row.get("loop_id") != loop.get("loop_id")]
    registry["closed"] = [row for row in registry.get("closed", []) if row.get("loop_id") != loop.get("loop_id")]
    if loop.get("status") in CLOSED_STATUSES:
        registry["closed"] = _replace_loop(registry.get("closed", []), loop)
    else:
        registry["open"] = _replace_loop(registry.get("open", []), loop)
    _write_json(root / REGISTRY_PATH, registry)
    _upsert_task_queue(root, loop)
    return loop


def _emit_lifecycle_email(root: Path, loop: dict[str, Any], phase: str) -> dict[str, Any]:
    try:
        from src.file_email_plugin_seq001_v001 import emit_prompt_lifecycle_email
        return emit_prompt_lifecycle_email(root, loop, phase=phase)
    except Exception as exc:
        return {"status": "error", "phase": phase, "error": str(exc)}


def _next_loop_task_id(tasks: list[dict[str, Any]]) -> str:
    nums = []
    for task in tasks:
        raw = str(task.get("id", ""))
        if raw.startswith("il-"):
            try:
                nums.append(int(raw.split("-", 1)[1]))
            except ValueError:
                pass
    return f"il-{(max(nums) if nums else 0) + 1:03d}"


def _task_status(loop_status: str) -> str:
    if loop_status in {"verified", "done", "resolved", "rejected", "abandoned"}:
        return "done"
    if loop_status in {"response_observed", "execution_observed", "waiting_for_copilot_execution"}:
        return "in_progress"
    return "pending"


def _upsert_task_queue(root: Path, loop: dict[str, Any]) -> None:
    path = root / "task_queue.json"
    data = _load_json(path)
    if not isinstance(data, dict):
        data = {"tasks": []}
    tasks = data.get("tasks") if isinstance(data.get("tasks"), list) else []
    loop_id = loop.get("loop_id")
    task = next((item for item in tasks if item.get("intent_loop_id") == loop_id), None)
    if task is None:
        task = {
            "id": _next_loop_task_id(tasks),
            "created_ts": loop.get("ts"),
            "completed_ts": None,
            "source": "intent_loop_closer",
            "intent_loop_id": loop_id,
        }
        tasks.append(task)
    task.update({
        "status": _task_status(str(loop.get("status") or "")),
        "title": loop.get("intent_key"),
        "intent": loop.get("prompt", "")[:300],
        "intent_key": loop.get("intent_key"),
        "scope": str(loop.get("intent_key", "root")).split(":", 1)[0],
        "stage": loop.get("stage"),
        "priority": "high" if loop.get("status") == "awaiting_operator_approval" else "medium",
        "focus_files": loop.get("focus_files", [])[:12],
        "verification_state": loop.get("status"),
        "human_position": loop.get("human_position"),
    })
    if task["status"] == "done" and not task.get("completed_ts"):
        task["completed_ts"] = loop.get("completed_ts") or loop.get("updated_ts")
    data["tasks"] = tasks
    _write_json(path, data)


def record_intent_loop(
    root: Path,
    prompt: str,
    context_selection: dict[str, Any] | None = None,
    file_sim: dict[str, Any] | None = None,
    prompt_brain: dict[str, Any] | None = None,
    source: str = "prompt",
    deleted_words: list[str] | None = None,
) -> dict[str, Any]:
    root = Path(root)
    prompt = str(prompt or "").strip()
    file_sim = file_sim if isinstance(file_sim, dict) else {}
    prompt_brain = prompt_brain if isinstance(prompt_brain, dict) else {}
    key = _intent_key(root, prompt, file_sim, prompt_brain)
    ts = _utc_now()
    proposals = _proposal_rows(file_sim)
    orchestrator = file_sim.get("orchestrator") if isinstance(file_sim.get("orchestrator"), dict) else {}
    loop = {
        "schema": "intent_loop/v1",
        "ts": ts,
        "loop_id": f"loop-{_digest(ts, key, prompt, source)}",
        "status": _loop_status(file_sim),
        "stage": "human_intent_compiled",
        "source": source,
        "prompt": prompt,
        "deleted_words": deleted_words or [],
        "intent_key": key,
        "human_position": "on_loop",
        "human_in_loop": False,
        "approval_required": bool(orchestrator.get("approval_required", True)),
        "auto_write_allowed": bool(orchestrator.get("auto_write_allowed", False)),
        "target_state": file_sim.get("target_state", "interlinked_source_state"),
        "context_confidence": (context_selection or {}).get("confidence", 0) if isinstance(context_selection, dict) else 0,
        "focus_files": _focus_files(context_selection, file_sim),
        "proposals": proposals,
        "observed_responses": [],
        "observed_edits": [],
        "actor_contract": {
            "human": "state intent, approve risky evolution, veto drift",
            "copilot": "execute bounded work from the active loop ticket",
            "repo_plugin": "compile intent, simulate file combinations, bind edits, validate, create training candidates",
            "deepseek": "draft deep rewrite jobs only after approval and consensus gates",
        },
        "next_actions": [
            "operator approves or narrows the active loop",
            "Copilot executes one bounded proposal against focus files",
            "repo plugin logs edits and validation back onto this loop",
            "verified loop becomes a training pair candidate",
        ],
    }
    loop["submission_email"] = _emit_lifecycle_email(root, loop, "submission")
    return _write_loop(root, loop, "opened")


def _active_loop(root: Path, loop_id: str | None = None) -> dict[str, Any] | None:
    if loop_id:
        registry = _load_registry(root)
        for row in list(registry.get("open", [])) + list(registry.get("closed", [])):
            if row.get("loop_id") == loop_id:
                return row
        return None
    latest = _load_json(root / LATEST_PATH)
    return latest if isinstance(latest, dict) else None


def bind_response_to_latest_loop(root: Path, response_entry: dict[str, Any]) -> dict[str, Any]:
    root = Path(root)
    loop = _active_loop(root)
    if not loop or loop.get("status") in CLOSED_STATUSES:
        return {"status": "skipped", "reason": "no_open_loop"}
    response = {
        "ts": response_entry.get("ts") or _utc_now(),
        "response_id": response_entry.get("response_id"),
        "summary": str(response_entry.get("response") or "")[:500],
        "prompt_match": str(response_entry.get("prompt") or "")[:240] == str(loop.get("prompt") or "")[:240],
    }
    loop.setdefault("observed_responses", []).append(response)
    loop["observed_responses"] = loop["observed_responses"][-12:]
    loop["status"] = "response_observed"
    loop["stage"] = "model_response_bound"
    binding = {
        "schema": "intent_loop_binding/v1",
        "kind": "response",
        "loop_id": loop.get("loop_id"),
        "intent_key": loop.get("intent_key"),
        **response,
    }
    _append_jsonl(root / BINDINGS_PATH, binding)
    _write_loop(root, loop, "response_bound")
    return binding


def _edit_alignment(loop: dict[str, Any], file_name: str) -> dict[str, Any]:
    file_name = str(file_name or "")
    proposal_files = {str(p.get("file") or "") for p in _as_list(loop.get("proposals"))}
    focus_files = {str(item or "") for item in _as_list(loop.get("focus_files"))}
    if file_name in proposal_files:
        return {"score": 1.0, "reason": "proposal_file"}
    if file_name in focus_files:
        return {"score": 0.75, "reason": "focus_file"}
    stem = Path(file_name).stem.lower()
    if stem and stem in str(loop.get("prompt") or "").lower():
        return {"score": 0.55, "reason": "prompt_file_stem"}
    return {"score": 0.35, "reason": "latest_open_loop"}


def bind_edit_to_latest_loop(root: Path, edit_record: dict[str, Any]) -> dict[str, Any]:
    root = Path(root)
    loop = _active_loop(root)
    if not loop or loop.get("status") in CLOSED_STATUSES:
        return {"status": "skipped", "reason": "no_open_loop"}
    file_name = str(edit_record.get("file") or "unknown")
    alignment = _edit_alignment(loop, file_name)
    edit = {
        "ts": edit_record.get("ts") or _utc_now(),
        "file": file_name,
        "why": str(edit_record.get("edit_why") or edit_record.get("why") or "")[:500],
        "source": edit_record.get("source", "codex_explicit"),
        "alignment": alignment,
    }
    loop.setdefault("observed_edits", []).append(edit)
    loop["observed_edits"] = loop["observed_edits"][-24:]
    loop["status"] = "execution_observed"
    loop["stage"] = "repo_plugin_bound_edit"
    binding = {
        "schema": "intent_loop_binding/v1",
        "kind": "edit",
        "loop_id": loop.get("loop_id"),
        "intent_key": loop.get("intent_key"),
        **edit,
    }
    _append_jsonl(root / BINDINGS_PATH, binding)
    _append_training_candidate(root, loop, edit)
    _write_loop(root, loop, "edit_bound")
    return binding


def _append_training_candidate(root: Path, loop: dict[str, Any], edit: dict[str, Any]) -> None:
    candidate = {
        "schema": "intent_loop_training_candidate/v1",
        "ts": _utc_now(),
        "loop_id": loop.get("loop_id"),
        "intent_key": loop.get("intent_key"),
        "prompt": loop.get("prompt"),
        "deleted_words": loop.get("deleted_words", []),
        "file": edit.get("file"),
        "why": edit.get("why"),
        "alignment": edit.get("alignment"),
        "status": "candidate_until_validation",
    }
    _append_jsonl(root / TRAINING_CANDIDATES_PATH, candidate)


def close_intent_loop(
    root: Path,
    loop_id: str | None = None,
    status: str = "verified",
    note: str = "",
    validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    root = Path(root)
    loop = _active_loop(root, loop_id)
    if not loop:
        return {"status": "skipped", "reason": "loop_not_found", "loop_id": loop_id}
    final_status = status if status in CLOSED_STATUSES else "verified"
    loop["status"] = final_status
    loop["stage"] = "closed"
    loop["completed_ts"] = _utc_now()
    loop["completion_note"] = note
    loop["validation"] = validation or {}
    loop["completion_email"] = _emit_lifecycle_email(root, loop, "completion")
    _append_jsonl(root / COMPLETIONS_PATH, {
        "schema": "intent_loop_completion/v1",
        "loop_id": loop.get("loop_id"),
        "intent_key": loop.get("intent_key"),
        "status": final_status,
        "note": note,
        "validation": validation or {},
        "ts": loop["completed_ts"],
    })
    return _write_loop(root, loop, "closed")


def intent_loop_summary(root: Path) -> dict[str, Any]:
    root = Path(root)
    latest = _active_loop(root)
    registry = _load_registry(root)
    return {
        "schema": "intent_loop_summary/v1",
        "latest": latest or {},
        "open_count": len(registry.get("open", [])),
        "closed_count": len(registry.get("closed", [])),
        "paths": {
            "latest": LATEST_PATH,
            "history": HISTORY_PATH,
            "bindings": BINDINGS_PATH,
            "completions": COMPLETIONS_PATH,
            "training_candidates": TRAINING_CANDIDATES_PATH,
        },
    }


def render_intent_loop_block(loop: dict[str, Any]) -> str:
    if not isinstance(loop, dict) or not loop:
        return ""
    lines = [
        "## Intent Loop",
        "",
        f"**LOOP_ID:** `{loop.get('loop_id', 'none')}`",
        f"**STATUS:** `{loop.get('status', 'unknown')}`  **HUMAN:** `{loop.get('human_position', 'on_loop')}`",
        f"**INTENT_KEY:** `{loop.get('intent_key', 'none')}`",
        f"**TARGET_STATE:** `{loop.get('target_state', 'interlinked_source_state')}`",
        f"**APPROVAL_REQUIRED:** `{loop.get('approval_required', True)}`",
        "",
        "**COPILOT_CONTRACT:** Execute only bounded work from this loop; validation can veto completion.",
        "",
        "**FOCUS_FILES:**",
    ]
    files = loop.get("focus_files") or []
    lines.extend([f"- `{item}`" for item in files[:8]] or ["- none"])
    proposals = loop.get("proposals") or []
    if proposals:
        lines.extend(["", "**PROPOSALS:**"])
        for proposal in proposals[:5]:
            lines.append(
                f"- `{proposal.get('file')}` 10Q={proposal.get('ten_q_score')} "
                f"guard={proposal.get('guard')} job={proposal.get('deepseek_job_id')}"
            )
    return "\n".join(lines)
