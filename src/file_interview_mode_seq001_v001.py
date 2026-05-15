"""File interview mode for Codex-assisted codebase questions.

Turns file comments, rename aliases, push-cycle traces, and pending context
questions into a direct "ask my files" transcript.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_QUESTIONS = [
    "What did you learn from the latest push?",
    "What do you think the fix is?",
    "Is your current path still paired to your identity after rename or split?",
]


def interview_files(
    root: Path,
    question: str = "",
    files: list[str] | None = None,
    limit: int = 8,
    write: bool = True,
) -> dict[str, Any]:
    """Ask selected files a question using local codebase memory."""
    root = Path(root).resolve()
    selected = _select_files(root, files or [], limit)
    questions = [question.strip()] if question.strip() else DEFAULT_QUESTIONS
    answers = [_answer_file(root, path, questions) for path in selected]
    report = {
        "schema": "file_interview/v1",
        "ts": _utcnow(),
        "question": question.strip() or " / ".join(DEFAULT_QUESTIONS),
        "files_interviewed": len(answers),
        "answers": answers,
        "summary": _summarize_answers(answers),
    }
    if write:
        _write_outputs(root, report)
    return report


def _answer_file(root: Path, path: Path, questions: list[str]) -> dict[str, Any]:
    rel = _rel(root, path)
    text = _safe_read(path)
    profile = _file_profile(text)
    comments = _comments_for_file(root, rel)
    context_questions = _context_questions_for_file(root, rel)
    alias = _alias_for_file(root, rel)
    push = _latest_push_cycle(root)
    risk = _risk_for_file(rel, text, alias, context_questions)
    fix = _proposed_fix(rel, questions, comments, context_questions, alias, risk)
    return {
        "file": rel,
        "question": " / ".join(questions),
        "file_says": profile["says"],
        "i_think_fix_is": fix,
        "evidence": {
            "prior_file_comments": comments[:3],
            "pending_context_questions": context_questions[:5],
            "latest_push_cycle": push,
        },
        "rename_identity": alias,
        "risk": risk,
        "codex_takeaway": _codex_takeaway(rel, fix, risk),
    }


def _select_files(root: Path, requested: list[str], limit: int) -> list[Path]:
    selected: list[Path] = []
    for item in requested:
        resolved = _resolve_file(root, item)
        if resolved and resolved not in selected:
            selected.append(resolved)
    if selected:
        return selected[:limit]

    for candidate in _recent_learning_files(root):
        resolved = _resolve_file(root, candidate)
        if resolved and resolved not in selected:
            selected.append(resolved)
        if len(selected) >= limit:
            break
    return selected


def _recent_learning_files(root: Path) -> list[str]:
    files: list[str] = []
    latest_policy = _load_json(root / "logs" / "operator_response_policy_latest.json") or {}
    for comment in latest_policy.get("file_comments") or []:
        value = comment.get("file") or comment.get("path")
        if value:
            files.append(str(value))

    push = _latest_push_cycle(root)
    for module in push.get("modules_touched") or []:
        match = _find_by_stem(root, str(module))
        if match:
            files.append(match)

    for row in _load_jsonl(root / "logs" / "context_requests.jsonl", limit=60):
        module = row.get("module")
        if module:
            match = _find_by_stem(root, str(module))
            if match:
                files.append(match)
    return list(dict.fromkeys(files))


def _resolve_file(root: Path, value: str) -> Path | None:
    normalized = str(value or "").strip().replace("\\", "/")
    if not normalized:
        return None
    direct = root / normalized
    if direct.exists() and direct.is_file():
        return direct
    alias = _alias_for_key(root, normalized)
    current = alias.get("current_file") if alias else ""
    if current:
        resolved = root / current
        if resolved.exists() and resolved.is_file():
            return resolved
    stem = Path(normalized).stem
    match = _find_by_stem(root, stem)
    return root / match if match else None


def _find_by_stem(root: Path, stem: str) -> str:
    clean = Path(stem).stem
    if not clean:
        return ""
    candidates = []
    for folder in ("src", "codex_compat", "pigeon_compiler", "tests", "scripts"):
        base = root / folder
        if not base.exists():
            continue
        for path in base.rglob("*.py"):
            if path.stem == clean or path.stem.startswith(clean):
                candidates.append(path)
    if not candidates:
        return ""
    candidates.sort(key=lambda item: (len(item.name), item.as_posix()))
    return _rel(root, candidates[0])


def _file_profile(text: str) -> dict[str, str]:
    stripped = text.lstrip()
    says = ""
    if stripped.startswith(('"""', "'''")):
        quote = stripped[:3]
        end = stripped.find(quote, 3)
        says = stripped[3:end].strip().splitlines()[0] if end > 3 else ""
    if not says:
        for line in text.splitlines():
            clean = line.strip()
            if clean:
                says = clean[:180]
                break
    return {"says": says or "I do not have a readable opening statement."}


def _comments_for_file(root: Path, rel: str) -> list[dict[str, Any]]:
    policy = _load_json(root / "logs" / "operator_response_policy_latest.json") or {}
    out = []
    for comment in policy.get("file_comments") or []:
        path = str(comment.get("file") or comment.get("path") or "").replace("\\", "/")
        if _same_identity(root, rel, path):
            out.append({
                "file_says": comment.get("file_says", ""),
                "file_fix_proposal": comment.get("file_fix_proposal", ""),
                "fix_grade": comment.get("fix_grade", {}),
            })
    return out


def _context_questions_for_file(root: Path, rel: str) -> list[str]:
    stem = Path(rel).stem
    questions: list[str] = []
    for row in _load_jsonl(root / "logs" / "context_requests.jsonl", limit=200):
        module = str(row.get("module") or "")
        if module and (stem.startswith(module) or module.startswith(stem) or module in stem):
            questions.extend(str(q) for q in row.get("questions") or [])
    return list(dict.fromkeys(questions))


def _alias_for_file(root: Path, rel: str) -> dict[str, Any]:
    alias = _alias_for_key(root, rel)
    if alias:
        return alias
    stem = Path(rel).stem
    aliases = _load_json(root / "logs" / "file_identity_aliases.json") or {}
    rows = aliases.get("aliases") or {}
    for key, row in rows.items():
        current = str(row.get("current_file") or "").replace("\\", "/")
        if current == rel or Path(current).stem == stem:
            return {"alias": key, **row}
    return {"current_file": rel, "current_files": [rel], "status": "no_alias_record"}


def _alias_for_key(root: Path, key: str) -> dict[str, Any]:
    aliases = _load_json(root / "logs" / "file_identity_aliases.json") or {}
    rows = aliases.get("aliases") or {}
    return rows.get(key) or rows.get(str(key).lstrip("./")) or {}


def _same_identity(root: Path, left: str, right: str) -> bool:
    if not left or not right:
        return False
    left = left.replace("\\", "/")
    right = right.replace("\\", "/")
    if left == right:
        return True
    left_alias = _alias_for_file(root, left)
    right_alias = _alias_for_file(root, right)
    left_files = set(left_alias.get("current_files") or [left_alias.get("current_file", left)])
    right_files = set(right_alias.get("current_files") or [right_alias.get("current_file", right)])
    return bool(left_files & right_files) or Path(left).stem == Path(right).stem


def _latest_push_cycle(root: Path) -> dict[str, Any]:
    rows = _load_jsonl(root / "logs" / "push_cycles.jsonl", limit=5)
    if not rows:
        return {}
    row = rows[-1]
    return {
        "commit": row.get("commit", ""),
        "cycle_number": row.get("cycle_number", 0),
        "sync_score": (row.get("sync") or {}).get("score"),
        "modules_touched": (row.get("copilot_signal") or {}).get("modules_touched", [])[:12],
        "coaching": row.get("coaching", {}),
    }


def _risk_for_file(rel: str, text: str, alias: dict[str, Any], questions: list[str]) -> dict[str, Any]:
    risks = []
    line_count = len(text.splitlines())
    if line_count > 200:
        risks.append("over_cap")
    if alias.get("status") == "no_alias_record":
        risks.append("identity_not_recorded")
    if questions:
        risks.append("pending_context_questions")
    if "_v001" in rel and "_d0510" not in rel:
        risks.append("possibly_stale_version")
    return {"level": "high" if "over_cap" in risks else ("medium" if risks else "low"), "items": risks}


def _proposed_fix(
    rel: str,
    questions: list[str],
    comments: list[dict[str, Any]],
    context_questions: list[str],
    alias: dict[str, Any],
    risk: dict[str, Any],
) -> str:
    for comment in comments:
        proposal = comment.get("file_fix_proposal")
        if proposal:
            return str(proposal)
    if "identity" in " ".join(questions).lower() or alias.get("status") == "no_alias_record":
        return "I think the fix is to refresh my alias record and verify imports against my current path."
    if "over_cap" in risk.get("items", []):
        return "I think the fix is to split me at stable function boundaries, then update lineage before tests run."
    if context_questions:
        return "I think the fix is to answer my pending context questions with docstrings or a focused test."
    return "I think the fix is to keep my current role, but record this interview as fresh operator-visible context."


def _codex_takeaway(rel: str, fix: str, risk: dict[str, Any]) -> str:
    return f"{rel} says: {fix} Risk is {risk.get('level')}."


def _summarize_answers(answers: list[dict[str, Any]]) -> dict[str, Any]:
    high = [a["file"] for a in answers if (a.get("risk") or {}).get("level") == "high"]
    pending = [a["file"] for a in answers if (a.get("evidence") or {}).get("pending_context_questions")]
    return {
        "high_risk_files": high,
        "files_with_pending_questions": pending,
        "top_takeaways": [a.get("codex_takeaway", "") for a in answers[:5]],
    }


def _write_outputs(root: Path, report: dict[str, Any]) -> None:
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    _append_jsonl(logs / "file_interviews.jsonl", report)
    (logs / "file_interview_latest.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (logs / "file_interview_latest.md").write_text(_render_markdown(report), encoding="utf-8")


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# File Interview",
        "",
        f"- ts: `{report.get('ts')}`",
        f"- question: {report.get('question')}",
        "",
    ]
    for answer in report.get("answers") or []:
        lines.extend([
            f"## `{answer.get('file')}`",
            f"- file says: {answer.get('file_says')}",
            f"- I think the fix is: {answer.get('i_think_fix_is')}",
            f"- risk: `{(answer.get('risk') or {}).get('level')}` {', '.join((answer.get('risk') or {}).get('items') or [])}",
            f"- current identity: `{(answer.get('rename_identity') or {}).get('current_file', '')}`",
            "",
        ])
    return "\n".join(lines)


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def _load_jsonl(path: Path, limit: int = 50) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines()[-limit:]:
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ask codebase files local interview questions.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--question", default="")
    parser.add_argument("--file", action="append", default=[])
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)
    result = interview_files(
        Path(args.root),
        question=args.question,
        files=args.file,
        limit=args.limit,
        write=not args.no_write,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
