"""Assemble and persist the operator response policy."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.operator_response_policy_comments_seq001_v001 import (
    _file_comment_synth,
    _focus_files,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _deepseek_response_policy_audit(
    file_comments: list[dict[str, Any]],
) -> dict[str, Any]:
    needs_deepseek = []
    for comment in file_comments:
        grade = comment.get("fix_grade") or {}
        if grade.get("decision") == "deepseek_should_draft_policy":
            needs_deepseek.append(comment.get("file"))
        if comment.get("selected_by") == "file_sim" and "blocked" in str(
            comment.get("file_signal")
        ):
            needs_deepseek.append(comment.get("file"))
    needs = [item for item in dict.fromkeys(needs_deepseek) if item]
    return {
        "schema": "deepseek_response_policy_audit/v1",
        "should_make_response_policy": bool(needs),
        "target_files": needs,
        "reason": (
            "Some file proposals are plausible but under-graded; DeepSeek should "
            "draft policy language before edit."
            if needs
            else "Local file comments and grader are sufficient; DeepSeek can wait "
            "for approved rewrite."
        ),
        "prompt": (
            "Draft response-policy wording that preserves file voice, grades proposed "
            "fixes, and records backward-pass path learning for the target files."
        ),
    }


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
    file_comments = _file_comment_synth(pack)
    file_comments_required = bool(focus)
    result = {
        "schema": "operator_response_policy/v1",
        "status": "ok",
        "ts": _utc_now(),
        "surface": surface,
        "active_arm": "opus_file_comments" if file_comments_required else "concise_codex",
        "operator_read": (
            "Opus synth active: files comment, propose fixes, get graded, and teach "
            "the backward path."
            if file_comments_required
            else "No selected files yet; keep response concise and concrete."
        ),
        "required_sections": ["File Comments"] if file_comments_required else [],
        "next_mutation": "Carry selected-file residue into the next dynamic context pack.",
        "intent_moves": [
            {
                "intent_key": "opus_instruction_layer",
                "move": "read first and reconcile with live context",
            },
            {
                "intent_key": "file_comments",
                "move": "write file voice, proposed fix, grade, action, and risk",
            },
            {
                "intent_key": "backward_pass_learning",
                "move": "record which path pattern caused selection",
            },
        ],
        "probe_files": [
            {"file": item.get("name"), "reason": item.get("reason") or "focus"}
            for item in focus[:8]
        ],
        "file_comments": file_comments,
        "deepseek_response_policy_audit": _deepseek_response_policy_audit(file_comments),
        "response_contract": {
            "file_comments_required": file_comments_required,
            "section_name": "File Comments",
            "format": (
                "`path`: File says -> I think the fix is -> grader -> Opus synth -> "
                "Codex did/learned -> backward path note."
            ),
        },
        "inject_requested": bool(inject),
    }
    if write:
        _write_policy(root, result)
    return result


def _write_policy(root: Path, result: dict[str, Any]) -> None:
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
        (
            "- file_comments_required: "
            f"`{result['response_contract']['file_comments_required']}`"
        ),
        "",
    ]
    for item in result["probe_files"]:
        lines.append(f"- `{item['file']}` via {item['reason']}")
    if result["file_comments"]:
        lines.extend(["", "## File Comments Synth", ""])
        for comment in result["file_comments"][:8]:
            lines.append(
                f"- `{comment['file']}`: {comment['file_signal']} | "
                f"{comment['file_fix_proposal']} | "
                f"grade `{comment['fix_grade']['decision']}`"
            )
    audit = result["deepseek_response_policy_audit"]
    lines.extend([
        "",
        "## DeepSeek Response Policy Audit",
        "",
        f"- should_make_response_policy: `{audit['should_make_response_policy']}`",
        f"- reason: {audit['reason']}",
    ])
    (logs / "operator_response_policy_latest.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    for comment in result["file_comments"]:
        _append_jsonl(
            logs / "file_solution_backward_pass.jsonl",
            comment["backward_pass_learning"],
        )


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
