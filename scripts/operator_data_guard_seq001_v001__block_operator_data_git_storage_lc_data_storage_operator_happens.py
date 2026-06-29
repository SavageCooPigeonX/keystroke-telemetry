"""Block operator-private runtime data from entering git.

Goal: operator data must live in MAIF or ignored local spools, never in commits.
Resolution: pre-push exits non-zero when staged/tracked paths violate the rule.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


BLOCKED_EXACT = {
    ".master_key", ".master_test_sha", ".overcap_budget", "agent_coaching.md",
    "file_heat_map.json", "file_profiles.json", "intent_backlog_resolutions.json",
    "operator_coaching.md", "operator_profile.md", "query_memory.json",
    "rework_log.json", "task_queue.json",
}

BLOCKED_DIRS = {
    ".maif/", ".personal/", "logs/", "test_logs/", "stress_logs/",
    "maif_operator_data/", "operator_data/", "operator_sessions/",
    "planning/private/", "private/",
}

BLOCKED_NAME_FRAGMENTS = {
    "chat_compositions", "deleted_words", "file_heat_map", "keystroke",
    "operator_profile", "operator_state", "prompt_journal", "query_memory",
    "rework_log", "telemetry_session", "typing_telemetry", "unsaid_thread",
}

DATA_SUFFIXES = {".db", ".json", ".jsonl", ".log", ".md", ".sqlite", ".sqlite3", ".txt"}

REQUIRED_GITIGNORE_PATTERNS = [
    ".maif/", "maif_operator_data/", "operator_data/", "operator_sessions/",
    "operator_profile.md", "query_memory.json", "rework_log.json",
    "task_queue.json", "logs/",
]

ALLOWED_DOCS = {"docs/operator_data_storage_contract.md"}


@dataclass(frozen=True)
class Finding:
    path: str
    source: str
    reason: str


def _norm(path: str) -> str:
    return path.replace("\\", "/").lstrip("./").lower()


def _run_git(root: Path, args: list[str]) -> list[str]:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(root),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git {' '.join(args)} failed")
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def classify_operator_data_path(path: str) -> str:
    normalized = _norm(path)
    name = normalized.rsplit("/", 1)[-1]
    suffix = Path(name).suffix.lower()
    if normalized in ALLOWED_DOCS:
        return ""
    if name in BLOCKED_EXACT or normalized in BLOCKED_EXACT:
        return "blocked exact operator data filename"
    for prefix in BLOCKED_DIRS:
        if normalized.startswith(prefix):
            return f"blocked operator data directory {prefix}"
    if suffix in DATA_SUFFIXES:
        for fragment in BLOCKED_NAME_FRAGMENTS:
            if fragment in normalized:
                return f"blocked operator data fragment {fragment}"
    return ""


def _staged_paths(root: Path) -> list[str]:
    return _run_git(root, ["diff", "--cached", "--name-only", "--diff-filter=ACMRTUXB"])


def _tracked_paths(root: Path) -> list[str]:
    return _run_git(root, ["ls-files"])


def _untracked_paths(root: Path) -> list[str]:
    return _run_git(root, ["ls-files", "--others", "--exclude-standard"])


def _gitignore_missing(root: Path) -> list[str]:
    gitignore = root / ".gitignore"
    text = gitignore.read_text(encoding="utf-8", errors="replace") if gitignore.exists() else ""
    lines = {line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")}
    return [pattern for pattern in REQUIRED_GITIGNORE_PATTERNS if pattern not in lines]


def audit_operator_data_storage(
    root: Path,
    *,
    include_untracked: bool = True,
) -> dict[str, object]:
    findings: list[Finding] = []
    for source, paths in (
        ("staged", _staged_paths(root)),
        ("tracked", _tracked_paths(root)),
        ("untracked", _untracked_paths(root) if include_untracked else []),
    ):
        for path in paths:
            reason = classify_operator_data_path(path)
            if reason:
                findings.append(Finding(path=path, source=source, reason=reason))
    for pattern in _gitignore_missing(root):
        findings.append(
            Finding(
                path=".gitignore",
                source="contract",
                reason=f"missing required ignore pattern {pattern}",
            )
        )
    return {
        "schema": "operator_data_git_guard/v1",
        "root": str(root),
        "storage_rule": "operator-private data must be stored in MAIF or ignored local spools, not git",
        "maif_allowed_local_spools": [".maif/", "maif_operator_data/"],
        "findings": [finding.__dict__ for finding in findings],
        "ok": not findings,
    }


def render_report(report: dict[str, object]) -> str:
    lines = [
        "Operator Data Git Guard",
        f"Rule: {report['storage_rule']}",
        f"Status: {'OK' if report['ok'] else 'BLOCKED'}",
    ]
    findings = report.get("findings") or []
    if findings:
        lines.append("Findings:")
        for item in findings:
            lines.append(f"- {item['source']}: {item['path']} ({item['reason']})")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--pre-push", action="store_true", help="block when findings exist")
    parser.add_argument("--staged-only", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    report = audit_operator_data_storage(root, include_untracked=not args.staged_only)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render_report(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
