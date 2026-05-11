"""Operator response policy for Codex dynamic context."""

# ── pigeon ────────────────────────────────────
# SEQ: 001 | VER: v002 | 311 lines | ~3,186 tokens
# DESC:   operator_response_policy_for_codex
# INTENT: feat_bind_keystroke_telemetry
# LAST:   2026-05-10 @ 776858d
# SESSIONS: 1
# ──────────────────────────────────────────────
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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _focus_files(context_pack: dict[str, Any]) -> list[dict[str, Any]]:
    files = context_pack.get("focus_files") if isinstance(context_pack, dict) else []
    return [item for item in (files or []) if isinstance(item, dict) and item.get("name")]


def _packet_by_file(context_pack: dict[str, Any]) -> dict[str, dict[str, Any]]:
    knowledge = context_pack.get("file_self_knowledge") if isinstance(context_pack, dict) else {}
    packets = knowledge.get("packets") if isinstance(knowledge, dict) else []
    return {
        str(packet.get("file") or ""): packet
        for packet in (packets or [])
        if isinstance(packet, dict) and packet.get("file")
    }


def _sim_by_file(context_pack: dict[str, Any]) -> dict[str, dict[str, Any]]:
    file_sim = context_pack.get("file_sim") if isinstance(context_pack, dict) else {}
    proposals = file_sim.get("proposals") if isinstance(file_sim, dict) else []
    return {
        str(proposal.get("path") or ""): proposal
        for proposal in (proposals or [])
        if isinstance(proposal, dict) and proposal.get("path")
    }


def _file_comment_synth(context_pack: dict[str, Any]) -> list[dict[str, Any]]:
    packets = _packet_by_file(context_pack)
    sim = _sim_by_file(context_pack)
    comments = []
    prompt = str(context_pack.get("prompt") or "")
    for item in _focus_files(context_pack)[:8]:
        file_name = str(item.get("name") or "")
        packet = packets.get(file_name, {})
        proposal = sim.get(file_name, {})
        reason = item.get("reason") or "focus"
        selected_by = "file_sim" if reason == "file_sim_proposal" or proposal else reason
        says = packet.get("file_quote") or "selected file has no opening comment yet"
        if proposal:
            file_signal = (
                f"file-sim selected me with interlink={proposal.get('interlink_score')} "
                f"and decision={proposal.get('decision')}"
            )
        else:
            file_signal = f"selected via {reason}"
        fix_proposal = _file_fix_proposal(file_name, prompt, reason, proposal, packet)
        fix_grade = _grade_file_fix(file_name, proposal, packet, fix_proposal)
        comments.append({
            "file": file_name,
            "selected_by": selected_by,
            "file_says": says,
            "file_signal": file_signal,
            "file_fix_proposal": fix_proposal,
            "fix_grade": fix_grade,
            "backward_pass_learning": _backward_pass_learning(file_name, prompt, reason, proposal, packet),
            "opus_synth": (
                f"{file_name} is responsible for {reason}; weigh its proposed fix, report the graded path, "
                "and leave backward-pass notes for future selection."
            ),
            "residue_comment": packet.get("residue_comment")
            or f"{file_name}: selected via {reason}; leave a durable response note.",
        })
    return comments


def _file_fix_proposal(
    file_name: str,
    prompt: str,
    reason: str,
    proposal: dict[str, Any],
    packet: dict[str, Any],
) -> str:
    if proposal.get("proposed_fix"):
        return f"I think the fix is: {proposal.get('proposed_fix')}"
    owns = ", ".join(packet.get("owns") or []) or _path_role(file_name)
    if proposal.get("decision") == "blocked":
        return "I think the fix is: hold this path until the missing or risky context is resolved."
    if file_name.endswith(".py"):
        return (
            "I think the fix is: inspect my imports, validation plan, and recent selection reason, "
            f"then patch the smallest function related to {owns}."
        )
    if file_name.endswith((".md", ".txt")):
        return "I think the fix is: update my operator-facing wording so the next pass can reuse the note."
    if file_name.endswith((".json", ".jsonl")):
        return "I think the fix is: preserve schema, append learning instead of overwriting history, then validate JSON."
    if prompt:
        return f"I think the fix is: use my role in `{prompt[:80]}` as context before editing adjacent files."
    return "I think the fix is: inspect me before edit and keep the change narrow."


def _grade_file_fix(
    file_name: str,
    proposal: dict[str, Any],
    packet: dict[str, Any],
    fix_proposal: str,
) -> dict[str, Any]:
    checks = [
        {"key": "has_fix_sentence", "passed": fix_proposal.startswith("I think the fix is:")},
        {"key": "file_exists", "passed": bool(packet.get("exists"))},
        {"key": "has_validation", "passed": bool(packet.get("validates_with"))},
        {"key": "has_file_voice", "passed": bool(packet.get("file_quote"))},
        {"key": "sim_or_context_reason", "passed": bool(proposal or packet)},
        {"key": "not_blocked", "passed": proposal.get("decision") != "blocked"},
        {"key": "source_or_doc_target", "passed": file_name.endswith((".py", ".md", ".txt", ".json", ".jsonl"))},
    ]
    score = sum(1 for check in checks if check["passed"])
    if proposal.get("ten_q", {}).get("passed"):
        score += 2
        checks.append({"key": "file_sim_ten_q_passed", "passed": True})
    if proposal.get("interlink_score", 0) and float(proposal.get("interlink_score") or 0) >= 0.55:
        score += 1
        checks.append({"key": "interlink_strong", "passed": True})
    max_score = len(checks)
    if score >= 7:
        decision = "codex_can_act_after_review"
    elif score >= 5:
        decision = "deepseek_should_draft_policy"
    else:
        decision = "hold_for_more_context"
    return {
        "schema": "file_fix_grader/v1",
        "score": score,
        "max_score": max_score,
        "decision": decision,
        "checks": checks,
    }


def _backward_pass_learning(
    file_name: str,
    prompt: str,
    reason: str,
    proposal: dict[str, Any],
    packet: dict[str, Any],
) -> dict[str, Any]:
    tokens = _tokens(" ".join([
        file_name,
        prompt,
        reason,
        str(proposal.get("proposed_fix") or ""),
        " ".join(packet.get("owns") or []),
    ]))
    return {
        "schema": "file_solution_backward_pass/v1",
        "path": file_name,
        "path_family": _path_role(file_name),
        "selection_reason": reason,
        "pattern_tokens": tokens[:12],
        "learned_route": (
            f"When prompt/path tokens include {', '.join(tokens[:4]) or 'this pattern'}, "
            f"try `{file_name}` before broader neighbors."
        ),
        "notes": [
            f"selected_by={reason}",
            f"fix_decision={proposal.get('decision', 'context_only')}",
            f"readiness={(packet.get('mutation_scope') or {}).get('readiness', 'unknown')}",
        ],
    }


def _deepseek_response_policy_audit(file_comments: list[dict[str, Any]]) -> dict[str, Any]:
    needs_deepseek = []
    for comment in file_comments:
        grade = comment.get("fix_grade") or {}
        if grade.get("decision") == "deepseek_should_draft_policy":
            needs_deepseek.append(comment.get("file"))
        if comment.get("selected_by") == "file_sim" and "blocked" in str(comment.get("file_signal")):
            needs_deepseek.append(comment.get("file"))
    needs = [item for item in dict.fromkeys(needs_deepseek) if item]
    return {
        "schema": "deepseek_response_policy_audit/v1",
        "should_make_response_policy": bool(needs),
        "target_files": needs,
        "reason": (
            "Some file proposals are plausible but under-graded; DeepSeek should draft policy language before edit."
            if needs
            else "Local file comments and grader are sufficient; DeepSeek can wait for approved rewrite."
        ),
        "prompt": (
            "Draft response-policy wording that preserves file voice, grades proposed fixes, "
            "and records backward-pass path learning for the target files."
        ),
    }


def _path_role(file_name: str) -> str:
    path = file_name.replace("\\", "/")
    if path.startswith("test_") or "/test_" in path:
        return "test"
    if path.startswith("src/"):
        return "source"
    if path.startswith("codex_compat"):
        return "compiled_codex_context"
    if path.endswith(".md"):
        return "operator_docs"
    if path.endswith((".json", ".jsonl")):
        return "memory_log"
    return "repo_file"


def _tokens(text: str) -> list[str]:
    raw = re.findall(r"[A-Za-z][A-Za-z0-9_]{2,}", str(text).lower().replace("_", " "))
    out = []
    for token in raw:
        if token not in out and token not in {"the", "and", "for", "with", "this", "that"}:
            out.append(token)
    return out


def build_operator_response_policy(
    root: Path,
    prompt: str,
    surface: str = "codex",
    context_pack: dict[str, Any] | None = None,
    inject: bool = True,
    write: bool = True,
) -> dict[str, Any]:
    root = Path(root)
    pack = context_pack or {}
    focus = _focus_files(pack)
    file_comments_required = bool(focus)
    file_comments = _file_comment_synth(pack)
    deepseek_audit = _deepseek_response_policy_audit(file_comments)

    result = {
        "schema": "operator_response_policy/v1",
        "status": "ok",
        "ts": _utc_now(),
        "surface": surface,
        "active_arm": "opus_file_comments" if file_comments_required else "concise_codex",
        "operator_read": (
            "Opus synth active: files comment, propose fixes, get graded, and teach the backward path."
            if file_comments_required
            else "No selected files yet; keep response concise and concrete."
        ),
        "required_sections": ["File Comments"] if file_comments_required else [],
        "next_mutation": "Carry selected-file residue into the next dynamic context pack.",
        "intent_moves": [
            {"intent_key": "opus_instruction_layer", "move": "read first and reconcile with live context"},
            {"intent_key": "file_comments", "move": "write file voice, proposed fix, grade, action, and risk"},
            {"intent_key": "backward_pass_learning", "move": "record which path pattern caused selection"},
        ],
        "probe_files": [
            {"file": item.get("name"), "reason": item.get("reason") or "focus"}
            for item in focus[:8]
        ],
        "file_comments": file_comments,
        "deepseek_response_policy_audit": deepseek_audit,
        "response_contract": {
            "file_comments_required": file_comments_required,
            "section_name": "File Comments",
            "format": "`path`: File says -> I think the fix is -> grader -> Opus synth -> Codex did/learned -> backward path note.",
        },
        "inject_requested": bool(inject),
    }

    if write:
        logs = root / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        (logs / "operator_response_policy_latest.json").write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        lines = [
            "# Operator Response Policy",
            "",
            f"- updated: `{result['ts']}`",
            f"- active_arm: `{result['active_arm']}`",
            f"- file_comments_required: `{file_comments_required}`",
            "",
        ]
        for item in result["probe_files"]:
            lines.append(f"- `{item['file']}` via {item['reason']}")
        if result["file_comments"]:
            lines.extend(["", "## File Comments Synth", ""])
            for comment in result["file_comments"][:8]:
                lines.append(
                    f"- `{comment['file']}`: {comment['file_signal']} | "
                    f"{comment['file_fix_proposal']} | grade `{comment['fix_grade']['decision']}`"
                )
        audit = result["deepseek_response_policy_audit"]
        lines.extend([
            "",
            "## DeepSeek Response Policy Audit",
            "",
            f"- should_make_response_policy: `{audit['should_make_response_policy']}`",
            f"- reason: {audit['reason']}",
        ])
        (logs / "operator_response_policy_latest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        for comment in result["file_comments"]:
            _append_jsonl(logs / "file_solution_backward_pass.jsonl", comment["backward_pass_learning"])
    return result


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
