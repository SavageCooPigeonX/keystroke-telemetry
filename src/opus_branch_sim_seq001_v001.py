"""Opus branch/worktree simulation jobs."""
# ── telemetry:pulse ──
# EDIT_TS:   None
# EDIT_HASH: None
# EDIT_WHY:  None
# EDIT_AUTHOR: None
# EDIT_STATE: idle
# ── /pulse ──
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "opus_branch_sim/v1"
LATEST = "logs/opus_branch_sim_latest.json"
HISTORY = "logs/opus_branch_sim.jsonl"
MARKDOWN = "logs/opus_branch_sim.md"


def simulate_opus_branch_job(
    root: Path,
    goal: str,
    *,
    target: str = "context_compression_rescue",
    write: bool = True,
) -> dict[str, Any]:
    """Create a branch-sim contract without mutating git state."""
    root = Path(root)
    current = _baseline(root)
    job_id = "obs-" + hashlib.sha1(f"{goal}|{target}|{current.get('head')}".encode("utf-8")).hexdigest()[:12]
    files = _target_files(target)
    result = {
        "schema": SCHEMA,
        "ts": _now(),
        "job_id": job_id,
        "goal": goal,
        "target": target,
        "orchestrator": "claude-opus",
        "branch_plan": {
            "base_head": current.get("head"),
            "branch": f"codex/opus-sim-{target.replace('_', '-')}",
            "worktree": f"../opus-sim-{job_id}",
            "mutates_git": False,
        },
        "original_monitor": {
            "watch": ["git diff --stat", "pytest gates", "compression stats", "manifest note"],
            "baseline": current,
            "veto": "Claude Opus compares branch output to original before apply",
        },
        "gemini_context_select": {
            "task": "select compression, manifest, file-intelligence, and validation files",
            "focus_files": files,
        },
        "deepseek_file_pairs": [_delegate(file, target) for file in files],
        "complex_test": _complex_test(target),
        "grader_manifest_write": _manifest_note(goal, files),
        "paths": {"latest": LATEST, "history": HISTORY, "markdown": MARKDOWN},
    }
    if write:
        _write_json(root / LATEST, result)
        _append_jsonl(root / HISTORY, result)
        (root / MARKDOWN).write_text(render_opus_branch_sim(result), encoding="utf-8")
    return result


def grade_opus_branch_sim(sim: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
    """Grade simulated branch evidence from original state."""
    required = set(sim.get("complex_test", {}).get("required_gates") or [])
    passed = set(evidence.get("passed_gates") or [])
    changed = set(evidence.get("changed_files") or [])
    allowed = {file for job in sim.get("deepseek_file_pairs") or [] for file in job.get("allowed_files", [])}
    missing = sorted(required - passed)
    out_of_scope = sorted(changed - allowed)
    accepted = not missing and not out_of_scope and bool(changed)
    return {
        "schema": "opus_branch_sim_grade/v1",
        "ts": _now(),
        "job_id": sim.get("job_id"),
        "accepted": accepted,
        "decision": "merge_candidate" if accepted else "continue_branch_sim",
        "missing_gates": missing,
        "out_of_scope": out_of_scope,
        "backward_learning": "record compression efficacy, manifest usefulness, and file delegate accuracy",
    }


def render_opus_branch_sim(sim: dict[str, Any]) -> str:
    lines = ["# Opus Branch Sim", "", f"- job: `{sim['job_id']}`", f"- goal: {sim['goal']}"]
    lines.append(f"- branch: `{sim['branch_plan']['branch']}`")
    lines.extend(["", "## File Delegates"])
    for job in sim.get("deepseek_file_pairs") or []:
        lines.append(f"- `{job['target_file']}` -> {job['mission']}")
    lines.extend(["", "## Complex Test"])
    for gate in sim.get("complex_test", {}).get("required_gates") or []:
        lines.append(f"- `{gate}`")
    lines.extend(["", "## Manifest Write", sim.get("grader_manifest_write", {}).get("markdown", "")])
    return "\n".join(lines) + "\n"


def _target_files(target: str) -> list[str]:
    if target == "context_compression_rescue":
        return [
            "src/context_compressor_seq001_v001.py",
            "src/opus_orchestrator_runtime_seq001_v001.py",
            "src/file_deepseek_delegate_seq001_v001.py",
            "tests/interlink/test_context_compressor.py",
        ]
    return ["src/file_intelligence_graph_seq001_v001.py", "test_file_intelligence_graph.py"]


def _delegate(file_path: str, target: str) -> dict[str, Any]:
    test = "tests/interlink/test_context_compressor.py" if "compressor" in file_path else "test_opus_orchestrator_runtime.py"
    return {
        "target_file": file_path,
        "mission": "make LLM-readable compressed context branch-safe" if target == "context_compression_rescue" else "improve file intelligence",
        "gemini": "choose minimal context and file goal",
        "deepseek": "draft patch plus matching test in branch artifact",
        "allowed_files": list(dict.fromkeys([file_path, test, "logs/opus_branch_sim.md"])),
    }


def _complex_test(target: str) -> dict[str, Any]:
    return {
        "name": target,
        "required_gates": [
            "py -m pytest tests/interlink/test_context_compressor.py -q",
            "py -m pytest test_opus_orchestrator_runtime.py test_file_deepseek_delegate.py -q",
            "py scripts/maintain_compliance.py --all",
            "git diff --check",
        ],
        "success_signal": "compressed artifacts are generated, token ratio improves, manifests receive Opus note",
    }


def _manifest_note(goal: str, files: list[str]) -> dict[str, Any]:
    md = "\n".join([
        "### Opus Branch Sim Contract",
        f"- goal: {goal}",
        f"- files: {', '.join(files)}",
        "- branch rule: DeepSeek may patch only in branch/worktree; Opus grades from original.",
        "- compression rule: code is a manifest/byproduct context object; LLM readability wins over human prettiness.",
    ])
    return {"targets": ["MANIFEST.md", "src/MANIFEST.md", "logs/opus_branch_sim.md"], "markdown": md}


def _baseline(root: Path) -> dict[str, Any]:
    stats = root / "build" / "compressed" / "STATS.json"
    return {"head": _read_head(root), "compression_stats": _json(stats)}


def _read_head(root: Path) -> str:
    head = root / ".git" / "HEAD"
    try:
        return head.read_text(encoding="utf-8").strip()[:120]
    except OSError:
        return ""


def _json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, sort_keys=True) + "\n")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
