"""Run approval-safe actual jobs from file self-knowledge packets.

The runner does not rewrite source. It executes real validation commands for
high-confidence file packets, records outcomes, and feeds the results back into
file self-sim learning outcomes so files can condense memory from tests.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "actual_job_runner/v1"


def run_actual_jobs(
    root: Path,
    limit: int = 8,
    write: bool = True,
    timeout_s: int = 45,
) -> dict[str, Any]:
    root = Path(root)
    packets = _load_packets(root)
    jobs = [_job_from_packet(root, packet) for packet in packets]
    jobs = [job for job in jobs if job.get("eligible")]
    jobs.sort(key=lambda item: (item.get("confidence", 0), item.get("test_count", 0)), reverse=True)
    selected = jobs[: max(1, int(limit or 8))]
    for job in selected:
        job["results"] = [_run_command(root, cmd, timeout_s=timeout_s) for cmd in job["commands"]]
        job["status"] = "passed" if all(item.get("returncode") == 0 for item in job["results"]) else "failed"
        job["outcome_reward"] = _reward_for_job(job)
        job["fix_assessment"] = _fix_assessment(job)
    result = {
        "schema": SCHEMA,
        "ts": _now(),
        "root": str(root),
        "selected_count": len(selected),
        "passed_count": sum(1 for job in selected if job.get("status") == "passed"),
        "failed_count": sum(1 for job in selected if job.get("status") == "failed"),
        "high_confidence_fixes": _high_confidence_fixes(root),
        "jobs": selected,
        "operator_read": _operator_read(selected),
        "paths": {
            "latest": "logs/actual_job_runner_latest.json",
            "history": "logs/actual_job_runner.jsonl",
            "markdown": "logs/actual_job_runner.md",
            "learning_outcomes": "logs/file_self_sim_learning_outcomes.jsonl",
        },
    }
    if write:
        logs = root / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        _write_json(logs / "actual_job_runner_latest.json", result)
        _append_jsonl(logs / "actual_job_runner.jsonl", result)
        (logs / "actual_job_runner.md").write_text(render_actual_job_runner(result), encoding="utf-8")
        _record_learning_outcomes(root, selected)
    return result


def render_actual_job_runner(result: dict[str, Any]) -> str:
    lines = [
        "# Actual Job Runner",
        "",
        result.get("operator_read", ""),
        "",
        f"- selected: `{result.get('selected_count', 0)}`",
        f"- passed: `{result.get('passed_count', 0)}`",
        f"- failed: `{result.get('failed_count', 0)}`",
        "",
        "## High Confidence Fixes",
        "",
    ]
    fixes = result.get("high_confidence_fixes") or []
    if fixes:
        for fix in fixes:
            lines.append(f"- `{fix.get('file')}` confidence `{fix.get('confidence')}`: {fix.get('reason')}")
    else:
        lines.append("- none; current safe lane found validation jobs, not source-fix targets")
    lines.extend(["", "## Jobs", ""])
    for job in result.get("jobs") or []:
        lines.extend([
            f"### {job.get('file')}",
            f"- confidence: `{job.get('confidence')}`",
            f"- status: `{job.get('status')}`",
            f"- reward: `{job.get('outcome_reward')}`",
            f"- assessment: {job.get('fix_assessment')}",
        ])
        for item in job.get("results") or []:
            lines.append(
                f"- `{item.get('command')}` -> `{item.get('returncode')}` "
                f"{item.get('stdout_tail') or item.get('stderr_tail') or ''}"
            )
        lines.append("")
    return "\n".join(lines)


def _load_packets(root: Path) -> list[dict[str, Any]]:
    data = _load_json(root / "logs" / "file_self_knowledge_latest.json") or {}
    return [item for item in data.get("packets") or [] if isinstance(item, dict)]


def _job_from_packet(root: Path, packet: dict[str, Any]) -> dict[str, Any]:
    rel = str(packet.get("file") or "").replace("\\", "/")
    scope = packet.get("mutation_scope") or {}
    commands = [_normalize_command(cmd) for cmd in packet.get("validates_with") or []]
    commands = [cmd for cmd in commands if _command_allowed(root, cmd)]
    test_count = sum(1 for cmd in commands if "pytest" in cmd or "py_compile" in cmd)
    known_failures = packet.get("known_failures") or []
    blocking_failures = _blocking_failures(known_failures)
    eligible = (
        bool(rel)
        and (root / rel).exists()
        and scope.get("readiness") == "draft_ready"
        and not blocking_failures
        and test_count > 0
        and bool(commands)
    )
    confidence = 0.35
    confidence += min(test_count, 5) * 0.09
    confidence += min(len(packet.get("relationships") or []), 4) * 0.04
    confidence += min((packet.get("source_evidence") or {}).get("identity_growth_events", 0), 10) * 0.01
    if rel.startswith("src/") or rel.startswith("client/"):
        confidence += 0.08
    if blocking_failures:
        confidence -= 0.3
    return {
        "file": rel,
        "packet_id": packet.get("packet_id"),
        "eligible": eligible,
        "confidence": round(min(max(confidence, 0.0), 0.98), 4),
        "commands": commands[:5],
        "test_count": test_count,
        "known_failures": known_failures,
        "blocking_failures": blocking_failures,
        "owns": packet.get("owns", [])[:6],
    }


def _blocking_failures(known_failures: list[str]) -> list[str]:
    advisory_prefixes = (
        "prior_learning_outcome:actual_job_fail",
        "prior_learning_outcome:actual_job_pass",
        "prior_learning_outcome:compile_pass",
        "prior_learning_outcome:passed",
        "prior_learning_outcome:verified",
    )
    return [
        item for item in known_failures
        if not any(str(item).startswith(prefix) for prefix in advisory_prefixes)
    ]


def _run_command(root: Path, command: str, timeout_s: int = 45) -> dict[str, Any]:
    parts = command.split()
    try:
        result = subprocess.run(
            parts,
            cwd=root,
            text=True,
            capture_output=True,
            timeout=timeout_s,
            check=False,
            encoding="utf-8",
            errors="replace",
        )
        return {
            "command": command,
            "returncode": result.returncode,
            "stdout_tail": _tail(result.stdout),
            "stderr_tail": _tail(result.stderr),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "returncode": 124,
            "stdout_tail": _tail(exc.stdout or ""),
            "stderr_tail": f"timeout after {timeout_s}s",
        }
    except Exception as exc:
        return {"command": command, "returncode": 125, "stdout_tail": "", "stderr_tail": str(exc)}


def _record_learning_outcomes(root: Path, jobs: list[dict[str, Any]]) -> None:
    try:
        from src.file_self_sim_learning_seq001_v001 import record_file_learning_outcome
    except Exception:
        record_file_learning_outcome = None
    for job in jobs:
        packet_id = str(job.get("packet_id") or "")
        if not packet_id:
            continue
        outcome = "actual_job_pass" if job.get("status") == "passed" else "actual_job_fail"
        details = {
            "source": SCHEMA,
            "file": job.get("file"),
            "commands": job.get("commands", []),
            "results": job.get("results", []),
            "fix_assessment": job.get("fix_assessment", ""),
        }
        if record_file_learning_outcome:
            try:
                record_file_learning_outcome(root, packet_id, outcome, reward=job.get("outcome_reward", 0), details=details)
                continue
            except Exception:
                pass
        _append_jsonl(root / "logs" / "file_self_sim_learning_outcomes.jsonl", {
            "schema": "file_self_sim_learning_outcome/v1",
            "ts": _now(),
            "packet_id": packet_id,
            "file": job.get("file"),
            "outcome": outcome,
            "reward": job.get("outcome_reward", 0),
            "details": details,
        })


def _high_confidence_fixes(root: Path) -> list[dict[str, Any]]:
    sim = _load_json(root / "logs" / "batch_rewrite_sim_latest.json") or {}
    fixes = []
    for proposal in sim.get("proposals") or []:
        if not isinstance(proposal, dict):
            continue
        rel = str(proposal.get("path") or "").replace("\\", "/")
        confidence = float(proposal.get("confidence") or 0)
        reward = float(proposal.get("reward") or 0)
        decision = proposal.get("decision")
        validation = proposal.get("validation_plan") or []
        real_validation = [cmd for cmd in validation if _command_allowed(root, _normalize_command(cmd))]
        if confidence >= 0.65 and reward >= 0.6 and decision == "safe_dry_run" and real_validation:
            fixes.append({
                "file": rel,
                "confidence": round(confidence, 4),
                "reward": round(reward, 4),
                "reason": proposal.get("proposed_fix", ""),
                "validation": real_validation[:4],
            })
    return fixes


def _fix_assessment(job: dict[str, Any]) -> str:
    if job.get("status") == "passed":
        return "no source fix needed; file earned stronger context-clearing/self-knowledge confidence"
    failed = [item for item in job.get("results") or [] if item.get("returncode") != 0]
    if not failed:
        return "unknown failure state"
    first = failed[0]
    text = f"{first.get('stdout_tail', '')}\n{first.get('stderr_tail', '')}".lower()
    if "syntaxerror" in text or "importerror" in text or "modulenotfounderror" in text:
        return "high-confidence repair candidate if failure is inside the target file/import path"
    return "test failed; needs diagnosis before autonomous patch"


def _operator_read(jobs: list[dict[str, Any]]) -> str:
    if not jobs:
        return "No eligible actual jobs found; current proposals are not safe enough to execute."
    passed = sum(1 for job in jobs if job.get("status") == "passed")
    failed = sum(1 for job in jobs if job.get("status") == "failed")
    return (
        f"Ran {len(jobs)} actual validation job(s): {passed} passed, {failed} failed. "
        "Passing jobs are not source fixes; they are confidence/reward evidence for files to clear context or accept bounded future patches."
    )


def _reward_for_job(job: dict[str, Any]) -> float:
    base = float(job.get("confidence") or 0)
    if job.get("status") == "passed":
        base += 0.18
    else:
        base -= 0.25
    return round(min(max(base, -1.0), 1.0), 4)


def _normalize_command(command: Any) -> str:
    text = str(command or "").strip()
    text = re.sub(r"\s+", " ", text)
    if text.startswith("python -m "):
        text = "py -m " + text[len("python -m "):]
    return text


def _command_allowed(root: Path, command: str) -> bool:
    parts = command.split()
    if not parts:
        return False
    if parts[:3] == ["py", "-m", "py_compile"] and len(parts) == 4:
        return _safe_existing_path(root, parts[3], suffixes={".py"})
    if parts[:3] == ["py", "-m", "pytest"] and len(parts) >= 4:
        target = parts[3]
        return _safe_existing_path(root, target, suffixes={".py"})
    if parts == ["git", "diff", "--check"]:
        return True
    return False


def _safe_existing_path(root: Path, value: str, suffixes: set[str]) -> bool:
    rel = value.replace("\\", "/")
    if rel.startswith("/") or ".." in Path(rel).parts:
        return False
    path = root / rel
    return path.exists() and path.suffix in suffixes


def _tail(text: str, limit: int = 400) -> str:
    text = str(text or "").strip().replace("\r\n", "\n")
    if len(text) <= limit:
        return text
    return text[-limit:]


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return None


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run high-confidence actual validation jobs.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--timeout-s", type=int, default=45)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)
    result = run_actual_jobs(Path(args.root), limit=args.limit, timeout_s=args.timeout_s, write=not args.no_write)
    print(json.dumps({
        "schema": result.get("schema"),
        "selected": result.get("selected_count"),
        "passed": result.get("passed_count"),
        "failed": result.get("failed_count"),
        "high_confidence_fixes": result.get("high_confidence_fixes"),
        "paths": result.get("paths"),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["run_actual_jobs", "render_actual_job_runner"]
