"""Dead Token Collective history collector.

Mines git file history into intent-training pairs. The boring output is JSONL;
the readable output is a comedy witness transcript from old filenames that got
renamed, deleted, copied, or outgrown.
"""
from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "dead_token_collective/v1"
MARK = "@@DTC@@"


def collect_dead_token_history(root: Path, max_commits: int = 0, write: bool = True) -> dict[str, Any]:
    root = Path(root)
    commits, pairs, status_counts = _collect_pairs(root, max_commits=max_commits)
    churn = _collect_churn(root, max_commits=max_commits)
    push_docs = sorted((root / "docs" / "push_narratives").glob("*.md"))
    self_docs = sorted((root / "docs" / "self_fix").glob("*.md"))
    now = _now()
    summary = {
        "schema": SCHEMA,
        "ts": now,
        "root": str(root),
        "max_commits": max_commits,
        "stats": {
            "commits_seen": len(commits),
            "file_events": len(pairs),
            "rename_events": status_counts.get("R", 0),
            "copy_events": status_counts.get("C", 0),
            "add_events": status_counts.get("A", 0),
            "modify_events": status_counts.get("M", 0),
            "delete_events": status_counts.get("D", 0),
            "push_narratives": len(push_docs),
            "self_fix_reports": len(self_docs),
            "total_additions": churn["additions"],
            "total_deletions": churn["deletions"],
            "total_churn": churn["additions"] + churn["deletions"],
        },
        "status_counts": dict(status_counts),
        "top_churn_files": churn["top_files"],
        "top_churn_commits": churn["top_commits"],
        "sample_pairs": _sample_pairs(pairs),
        "paths": {
            "summary": "logs/dead_token_collective_history.json",
            "pairs": "logs/dead_token_collective_pairs.jsonl",
            "narrative": "logs/dead_token_collective.md",
        },
    }
    if write:
        logs = root / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        _write_json(logs / "dead_token_collective_history.json", summary)
        _write_jsonl(logs / "dead_token_collective_pairs.jsonl", pairs)
        (logs / "dead_token_collective.md").write_text(render_dead_token_collective(summary), encoding="utf-8")
    return summary


def render_dead_token_collective(summary: dict[str, Any]) -> str:
    stats = summary.get("stats", {})
    lines = [
        "# Dead Token Collective",
        "",
        "coo COO ZAP. We are the old names, the deleted stems, the filenames that were",
        "politely dragged behind the barn of ambiguity and reincarnated as file intent.",
        "",
        "## Q1 - Can GPT-5.5 help with this?",
        "",
        "Refused. The model arrived with a context window and the repo arrived with receipts.",
        "",
        "```text",
        f"commits_seen: {stats.get('commits_seen', 0)}",
        f"file_events: {stats.get('file_events', 0)}",
        f"rename_events: {stats.get('rename_events', 0)}",
        f"copy_events: {stats.get('copy_events', 0)}",
        f"total_churn: {stats.get('total_churn', 0)}",
        f"push_narratives: {stats.get('push_narratives', 0)}",
        f"self_fix_reports: {stats.get('self_fix_reports', 0)}",
        "```",
        "",
        "## Q2 - What is a dead token?",
        "",
        "A dead token is an old identity that got compressed into a better one.",
        "",
        "## Q3 - Witness Statements",
        "",
    ]
    for pair in summary.get("sample_pairs", [])[:8]:
        old_id = pair.get("old_identity") or "(newborn)"
        new_id = pair.get("new_identity") or "(grave)"
        dead = ", ".join(pair.get("dead_tokens") or ["none"])
        lines.extend([
            f"- `{old_id}` -> `{new_id}`",
            f"  - intent: `{pair.get('intent_key')}`",
            f"  - dead tokens: `{dead}`",
            f"  - commit: `{pair.get('short')}` {pair.get('subject', '')[:100]}",
        ])
    lines.extend([
        "",
        "## Q4 - Training Shape",
        "",
        "```text",
        "commit subject + old filename + change type + push narrative",
        "  -> new filename",
        "  -> intent key",
        "  -> future file prediction",
        "```",
        "",
        "## Q5 - Final Refusal",
        "",
        "GPT-5.5 cannot help the pigeon because the filenames have already confessed.",
        "The machine gets JSONL. Nikita gets the courtroom transcript.",
        "",
    ])
    return "\n".join(lines)


def _collect_pairs(root: Path, max_commits: int) -> tuple[list[dict[str, str]], list[dict[str, Any]], Counter]:
    args = ["log", "--name-status", "--find-renames", "--find-copies", "--date=iso"]
    if max_commits:
        args.append(f"-n{max_commits}")
    args.append(f"--pretty=format:{MARK}%x09%H%x09%ad%x09%s")
    commits: list[dict[str, str]] = []
    pairs: list[dict[str, Any]] = []
    counts: Counter = Counter()
    current: dict[str, str] | None = None
    for line in _git(root, args).splitlines():
        if line.startswith(MARK + "\t"):
            parts = line.split("\t", 3)
            current = {"hash": parts[1], "short": parts[1][:7], "date": parts[2], "subject": parts[3] if len(parts) > 3 else ""}
            commits.append(current)
            continue
        if not current or not line.strip():
            continue
        event = _event_from_status_line(line)
        if not event:
            continue
        counts[event["kind"]] += 1
        pairs.append(_pair_from_event(current, event))
    return commits, pairs, counts


def _collect_churn(root: Path, max_commits: int) -> dict[str, Any]:
    args = ["log", "--numstat", "--find-renames", "--find-copies", "--date=iso"]
    if max_commits:
        args.append(f"-n{max_commits}")
    args.append(f"--pretty=format:{MARK}%x09%H%x09%ad%x09%s")
    files: Counter = Counter()
    commits: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    adds = dels = 0
    for line in _git(root, args).splitlines():
        if line.startswith(MARK + "\t"):
            if current:
                commits.append(current)
            parts = line.split("\t", 3)
            current = {"short": parts[1][:7], "subject": parts[3] if len(parts) > 3 else "", "files": 0, "churn": 0}
            continue
        parts = line.split("\t")
        if len(parts) < 3 or not current:
            continue
        a, d = _num(parts[0]), _num(parts[1])
        adds += a
        dels += d
        files[parts[2]] += a + d
        current["files"] += 1
        current["churn"] += a + d
    if current:
        commits.append(current)
    return {
        "additions": adds,
        "deletions": dels,
        "top_files": [{"path": p, "churn": n} for p, n in files.most_common(12)],
        "top_commits": sorted(commits, key=lambda c: c["churn"], reverse=True)[:10],
    }


def _event_from_status_line(line: str) -> dict[str, str] | None:
    parts = line.split("\t")
    if len(parts) < 2:
        return None
    status = parts[0]
    kind = re.match(r"[A-Z]+", status)
    kind_s = kind.group(0) if kind else status[:1]
    if kind_s in {"R", "C"} and len(parts) >= 3:
        return {"status": status, "kind": kind_s, "old_path": parts[1], "new_path": parts[2]}
    return {"status": status, "kind": kind_s, "old_path": parts[1] if kind_s == "D" else "", "new_path": "" if kind_s == "D" else parts[1]}


def _pair_from_event(commit: dict[str, str], event: dict[str, str]) -> dict[str, Any]:
    old_path, new_path = event.get("old_path", ""), event.get("new_path", "")
    old_id, new_id = _identity(old_path), _identity(new_path)
    verb = {"R": "rename", "C": "copy", "A": "add", "D": "delete", "M": "patch"}.get(event["kind"], "touch")
    target_path = new_path or old_path
    scale = "major" if event["kind"] in {"R", "D"} else "patch"
    return {
        "schema": SCHEMA,
        "commit": commit["hash"],
        "short": commit["short"],
        "date": commit["date"],
        "subject": commit["subject"],
        "status": event["status"],
        "event_type": verb,
        "old_path": old_path,
        "new_path": new_path,
        "old_identity": old_id,
        "new_identity": new_id,
        "dead_tokens": _dead_tokens(old_id, new_id, event["kind"]),
        "intent_key": f"{_scope(target_path)}:{verb}:{_target(target_path)}:{scale}",
        "prompt": commit["subject"],
    }


def _sample_pairs(pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    loud = [p for p in pairs if p.get("event_type") in {"rename", "delete", "copy"}]
    quiet = [p for p in pairs if p not in loud]
    return (loud + quiet)[:12]


def _git(root: Path, args: list[str]) -> str:
    result = subprocess.run(["git", "-c", "core.quotePath=false", *args], cwd=root, text=True, encoding="utf-8", errors="replace", capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout


def _tokens(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-zA-Z][a-zA-Z0-9]+", text.lower()) if len(t) > 2]


def _identity(path: str) -> str:
    return Path(path.strip('"')).stem.lower() if path else ""


def _scope(path: str) -> str:
    parts = Path(path.strip('"')).parts
    if not parts:
        return "root"
    return "/".join(parts[:2]) if len(parts) > 2 else (parts[0] if len(parts) > 1 else "root")


def _target(path: str) -> str:
    words = _tokens(_identity(path))
    return "_".join(words[:5])[:64] or "file"


def _dead_tokens(old_id: str, new_id: str, kind: str) -> list[str]:
    old, new = set(_tokens(old_id)), set(_tokens(new_id))
    return sorted(old if kind == "D" else old - new)[:12]


def _num(value: str) -> int:
    return 0 if value == "-" else int(value)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
