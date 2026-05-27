"""Hourly autonomous file-sim execution contract.

This is the narrow loop that lets a long-running agent act once per hour
without pretending the codebase is ready for blind source rewrites.

The job of v1 is:
- run the learning-mode file sim,
- pick exactly one bounded maintenance action,
- emit a DeepSeek-ready context pack,
- record what the next hour should try.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.file_self_sim_learning_seq001_v001 import simulate_file_self_learning


SCHEMA = "hourly_autonomous_file_sim/v1"
PACK_SCHEMA = "hourly_deepseek_context_pack/v1"
DEFAULT_INTENT = (
    "hourly autonomous file sim organization pigeon code compliance manifest "
    "chain context compression debug sim"
)


def run_hourly_autonomous_file_sim(
    root: Path,
    intent: str = "",
    *,
    limit: int = 8,
    write: bool = True,
    run_validation: bool = False,
    sim_config: dict[str, Any] | None = None,
    source_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run one bounded autonomous maintenance cycle.

    This function does not overwrite source files. It converts the current
    sim state into a single action packet that Codex, Copilot, or DeepSeek can
    use for the next approved move.
    """
    root = Path(root)
    active_intent = _clean_intent(intent) or DEFAULT_INTENT
    sim = simulate_file_self_learning(
        root,
        active_intent,
        limit=limit,
        write=write,
        source_result=source_result,
        config=sim_config,
    )
    action = _select_hourly_action(root, sim)
    context_pack = _build_deepseek_context_pack(root, active_intent, sim, action)
    validation = _validation_receipt(root, action)
    if run_validation:
        validation["validation_execution"] = "requested"
        validation["executed"] = _run_validation_plan(root, action.get("validation_plan") or [])
        validation["validation_passed"] = bool(validation["executed"]) and all(
            item.get("status") == "passed" for item in validation["executed"]
        )
    result = {
        "schema": SCHEMA,
        "ts": _now(),
        "root": str(root),
        "mode": "one_intent_aligned_action_per_hour",
        "write_policy": "no_source_overwrite_without_explicit_approval",
        "intent": active_intent,
        "intent_key": action["intent_key"],
        "selected_action": action,
        "sim_debug": _sim_debug(sim),
        "deepseek_context_pack": context_pack,
        "validation": validation,
        "next_hour_seed": _next_hour_seed(action, sim),
        "paths": {
            "latest": "logs/hourly_autonomous_file_sim_latest.json",
            "history": "logs/hourly_autonomous_file_sim.jsonl",
            "markdown": "logs/hourly_autonomous_file_sim.md",
            "deepseek_context_pack": "logs/hourly_deepseek_context_pack.json",
        },
    }
    if write:
        _write_outputs(root, result)
    return result


def _select_hourly_action(root: Path, sim: dict[str, Any]) -> dict[str, Any]:
    split_jobs = list(sim.get("overcap_split_jobs") or [])
    graph = sim.get("relationship_graph") or {}
    registry = sim.get("architecture_sequence_registry") or {}

    ready = [
        job for job in split_jobs
        if job.get("status") == "ready_for_split_plan"
    ]
    blocked = [
        job for job in split_jobs
        if str(job.get("status", "")).startswith("blocked")
    ]

    if ready:
        job = _highest_pressure_job(ready)
        return _split_plan_action(root, job, sim)

    if blocked:
        job = _highest_pressure_job(blocked)
        return _validation_mapping_action(root, job, sim)

    if _relationship_graph_needs_learning(graph):
        return _relationship_learning_action(sim)

    if _registry_has_pressure(registry):
        return _registry_compression_action(registry, sim)

    return _quiet_checkpoint_action(sim)


def _split_plan_action(root: Path, job: dict[str, Any], sim: dict[str, Any]) -> dict[str, Any]:
    target = job.get("file") or "unknown"
    context = _unique_strings([
        target,
        *(job.get("context_pack") or []),
        *_related_files_for(target, sim),
    ])
    tests = _validation_plan_for(root, target, job)
    return {
        "action_type": "deepseek_split_plan_context",
        "status": "ready",
        "intent_key": _intent_key(target, "split_plan", "organization"),
        "target_file": target,
        "reason": "over-cap file has enough validation/context to ask DeepSeek for a split plan",
        "bounded_action": "draft a split plan only; do not rewrite source",
        "context_files": context,
        "validation_plan": tests,
        "approval_gate": "operator_required_before_source_mutation",
        "deepseek_mode": "split_plan_only_no_source_write",
        "operator_read": (
            f"{target} is too large for the small-file/self-sim theory, but it has "
            "enough context to plan a split without touching source."
        ),
        "file_quote": _file_quote(
            target,
            "I am not asking to be rewritten. I am asking for a floor plan before somebody moves a wall.",
        ),
    }


def _validation_mapping_action(root: Path, job: dict[str, Any], sim: dict[str, Any]) -> dict[str, Any]:
    target = job.get("file") or "unknown"
    context = _unique_strings([
        target,
        *(job.get("context_pack") or []),
        *_related_files_for(target, sim),
    ])
    return {
        "action_type": "map_validation_for_overcap_file",
        "status": "blocked",
        "intent_key": _intent_key(target, "map_validation", "organization"),
        "target_file": target,
        "reason": "file is over cap, but the sim cannot prove a test gate yet",
        "bounded_action": "find or create the smallest validation gate before any split plan",
        "context_files": context,
        "validation_plan": _validation_plan_for(root, target, job),
        "approval_gate": "operator_required_before_source_mutation",
        "deepseek_mode": "validation_gate_mapping_only",
        "operator_read": (
            f"{target} wants a split, but the hourly loop should first teach the sim "
            "which test proves it survived."
        ),
        "file_quote": _file_quote(
            target,
            "Do not give me surgery until someone can locate my pulse.",
        ),
    }


def _relationship_learning_action(sim: dict[str, Any]) -> dict[str, Any]:
    wake = sim.get("wake_order") or []
    target = (wake[0] or {}).get("file") if wake else "logs/file_relationship_graph.json"
    return {
        "action_type": "improve_file_relationship_graph",
        "status": "learning",
        "intent_key": _intent_key(target or "relationship_graph", "learn_edges", "sim_debug"),
        "target_file": target or "logs/file_relationship_graph.json",
        "reason": "relationship graph is too thin for confident future file choreography",
        "bounded_action": "mine imports, tests, manifests, and memory links; do not rewrite source",
        "context_files": _unique_strings([target or "", "logs/file_relationship_graph.json"]),
        "validation_plan": ["py -m pytest test_file_self_sim_learning.py -q"],
        "approval_gate": "safe_log_update_only",
        "deepseek_mode": "relationship_extraction_only",
        "operator_read": "The next useful move is making the sim better at deciding who wakes with whom.",
        "file_quote": _file_quote(
            str(target or "relationship graph"),
            "I am tired of being introduced to coworkers by vibes and import errors.",
        ),
    }


def _registry_compression_action(registry: dict[str, Any], sim: dict[str, Any]) -> dict[str, Any]:
    summary = registry.get("summary") or {}
    critical = int(summary.get("critical") or 0)
    over_soft = int(summary.get("over_soft") or 0)
    return {
        "action_type": "compress_architecture_registry_pressure",
        "status": "learning",
        "intent_key": "architecture_registry:compress:size_pressure:organization",
        "target_file": "logs/file_identity_registry.json",
        "reason": f"registry reports {critical} critical and {over_soft} over-soft files",
        "bounded_action": "summarize size pressure into ranked jobs and next-hour seeds",
        "context_files": ["logs/file_identity_registry.json", "logs/overcap_split_jobs.json"],
        "validation_plan": ["py -m pytest test_file_self_sim_learning.py -q"],
        "approval_gate": "safe_log_update_only",
        "deepseek_mode": "registry_compression_only",
        "operator_read": "The repo pressure is real; compress it into fewer, better next moves.",
        "file_quote": _file_quote(
            "file_identity_registry.json",
            "I counted the swollen files and frankly everybody needs hydration and boundaries.",
        ),
    }


def _quiet_checkpoint_action(sim: dict[str, Any]) -> dict[str, Any]:
    return {
        "action_type": "quiet_checkpoint",
        "status": "no_high_confidence_mutation",
        "intent_key": "hourly_sim:checkpoint:no_safe_mutation:read",
        "target_file": "logs/hourly_autonomous_file_sim_latest.json",
        "reason": "no split, validation, relationship, or registry action cleared the confidence gate",
        "bounded_action": "record checkpoint and wait for stronger operator or sim signal",
        "context_files": [
            "logs/file_self_sim_learning_latest.json",
            "logs/file_relationship_graph.json",
            "logs/file_identity_registry.json",
        ],
        "validation_plan": ["py -m pytest test_file_self_sim_learning.py -q"],
        "approval_gate": "no_source_mutation",
        "deepseek_mode": "checkpoint_only",
        "operator_read": "Nothing should mutate this hour; the sim should admit uncertainty cleanly.",
        "file_quote": _file_quote(
            "hourly sim",
            "I did not touch production because I enjoy being alive in the morning.",
        ),
    }


def _build_deepseek_context_pack(
    root: Path,
    intent: str,
    sim: dict[str, Any],
    action: dict[str, Any],
) -> dict[str, Any]:
    target = action.get("target_file") or ""
    packets = [
        packet for packet in sim.get("learning_packets") or []
        if packet.get("file") == target
    ]
    return {
        "schema": PACK_SCHEMA,
        "pack_id": _stable_id("hourly", intent, target, action.get("action_type")),
        "ts": _now(),
        "role": "draft_or_plan_only_until_operator_approval",
        "operator_goal": (
            "debug the sim and hourly autonomous action loop; start with organization, "
            "code compliance, manifest chaining, context compression, and file identity growth"
        ),
        "selected_intent": intent,
        "selected_action": action,
        "learning_packets": packets[:2],
        "relationship_edges": _edges_for(target, sim)[:8],
        "manifest_or_memory_context": _existing_paths(root, action.get("context_files") or [])[:16],
        "deepseek_prompt": _deepseek_prompt(intent, action),
        "must_not_do": [
            "overwrite source without explicit operator approval",
            "split a file without a validation gate",
            "invent tests that were not run",
            "discard existing file memory or operator style signals",
        ],
        "required_output": [
            "sim diagnosis",
            "one bounded file/action proposal",
            "context files required",
            "validation gate",
            "backward learning note for future sims",
        ],
    }


def _deepseek_prompt(intent: str, action: dict[str, Any]) -> str:
    return (
        "You are the draft engine for an hourly file-sim loop. "
        f"Operator intent: {intent}. "
        f"Selected action: {action.get('action_type')} for {action.get('target_file')}. "
        f"Bounded action: {action.get('bounded_action')}. "
        "Return a plan or tiny patch proposal only. Keep file identity, validation, "
        "and interlinked source state as first-class constraints."
    )


def _sim_debug(sim: dict[str, Any]) -> dict[str, Any]:
    registry = sim.get("architecture_sequence_registry") or {}
    graph = sim.get("relationship_graph") or {}
    split_jobs = sim.get("overcap_split_jobs") or []
    return {
        "wake_count": len(sim.get("wake_order") or []),
        "learning_packet_count": len(sim.get("learning_packets") or []),
        "relationship_edge_count": len(graph.get("edges") or []),
        "split_job_count": len(split_jobs),
        "registry_summary": registry.get("summary") or {},
        "top_wakers": [
            node.get("file") for node in (sim.get("wake_order") or [])[:5]
        ],
        "top_split_jobs": [
            {
                "file": job.get("file"),
                "status": job.get("status"),
                "split_pressure": job.get("split_pressure"),
            }
            for job in split_jobs[:5]
        ],
    }


def _validation_receipt(root: Path, action: dict[str, Any]) -> dict[str, Any]:
    paths = action.get("context_files") or []
    existing = _existing_paths(root, paths)
    missing = [path for path in paths if path and path not in existing]
    return {
        "schema": "hourly_autonomous_validation_receipt/v1",
        "source_mutation": "none",
        "validation_execution": "not_requested",
        "context_files_existing": existing,
        "context_files_missing": missing[:12],
        "validation_plan": action.get("validation_plan") or [],
        "ready_for_source_mutation": False,
        "reason": "hourly v1 emits an approved context/action packet before mutation",
    }


def _run_validation_plan(root: Path, plan: list[str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for command in plan[:3]:
        command = str(command or "").strip()
        if not _is_safe_validation_command(command):
            results.append({
                "command": command,
                "status": "skipped",
                "reason": "command_not_in_safe_validation_allowlist",
            })
            continue
        try:
            completed = subprocess.run(
                command,
                cwd=root,
                shell=True,
                capture_output=True,
                text=True,
                timeout=180,
            )
        except subprocess.TimeoutExpired:
            results.append({
                "command": command,
                "status": "timeout",
                "returncode": None,
                "stdout_tail": "",
                "stderr_tail": "validation timed out after 180 seconds",
            })
            continue
        results.append({
            "command": command,
            "status": "passed" if completed.returncode == 0 else "failed",
            "returncode": completed.returncode,
            "stdout_tail": _tail(completed.stdout),
            "stderr_tail": _tail(completed.stderr),
        })
    return results


def _is_safe_validation_command(command: str) -> bool:
    if not command:
        return False
    banned = [";", "&&", "||", "|", ">", "<", "\n", "\r", "`"]
    if any(token in command for token in banned):
        return False
    normalized = " ".join(command.split()).lower()
    return (
        normalized.startswith("py -m py_compile ")
        or normalized.startswith("python -m py_compile ")
        or normalized.startswith("py -m pytest ")
        or normalized.startswith("python -m pytest ")
    )


def _tail(text: str, limit: int = 1200) -> str:
    text = str(text or "").strip()
    if len(text) <= limit:
        return text
    return text[-limit:]


def _next_hour_seed(action: dict[str, Any], sim: dict[str, Any]) -> dict[str, Any]:
    return {
        "intent": "continue hourly file sim; close the selected action or downgrade it with evidence",
        "preferred_next_action": action.get("action_type"),
        "target_file": action.get("target_file"),
        "carry_forward_files": action.get("context_files") or [],
        "carry_forward_signal": action.get("reason"),
        "debug_question": _debug_question(action, sim),
    }


def _debug_question(action: dict[str, Any], sim: dict[str, Any]) -> str:
    if action.get("action_type") == "deepseek_split_plan_context":
        return "Did the split plan identify a facade, children, and a validation gate without rewriting source?"
    if action.get("action_type") == "map_validation_for_overcap_file":
        return "Can the sim now prove which test owns this file before planning a split?"
    if action.get("action_type") == "improve_file_relationship_graph":
        return "Did the new edges make wake order less vibes-based and more evidence-based?"
    return "Did this hour reduce uncertainty or should the next hour choose a different action?"


def _render_markdown(result: dict[str, Any]) -> str:
    action = result["selected_action"]
    debug = result["sim_debug"]
    lines = [
        "# Hourly Autonomous File Sim",
        "",
        f"- intent key: `{result['intent_key']}`",
        f"- selected action: `{action['action_type']}`",
        f"- target: `{action.get('target_file')}`",
        f"- status: `{action.get('status')}`",
        f"- source mutation: `{result['validation']['source_mutation']}`",
        "",
        "## Operator Read",
        "",
        action.get("operator_read") or action.get("reason") or "",
        "",
        "## Sim Debug",
        "",
        f"- wake count: {debug.get('wake_count')}",
        f"- learning packets: {debug.get('learning_packet_count')}",
        f"- relationship edges: {debug.get('relationship_edge_count')}",
        f"- split jobs: {debug.get('split_job_count')}",
        f"- registry summary: `{json.dumps(debug.get('registry_summary') or {}, sort_keys=True)}`",
        "",
        "## Next Mutation",
        "",
        action.get("bounded_action") or "",
        "",
        "## Context Pack",
        "",
    ]
    for path in action.get("context_files") or []:
        lines.append(f"- `{path}`")
    lines.extend([
        "",
        "## Validation",
        "",
    ])
    for item in action.get("validation_plan") or []:
        lines.append(f"- `{item}`")
    executed = result.get("validation", {}).get("executed") or []
    if executed:
        lines.extend(["", "### Executed", ""])
        for item in executed:
            lines.append(f"- `{item.get('command')}` -> `{item.get('status')}`")
    lines.extend([
        "",
        "## File Quote",
        "",
        action.get("file_quote") or "",
        "",
        "## Next Hour Seed",
        "",
        f"- target: `{result['next_hour_seed'].get('target_file')}`",
        f"- question: {result['next_hour_seed'].get('debug_question')}",
        "",
    ])
    return "\n".join(lines)


def _write_outputs(root: Path, result: dict[str, Any]) -> None:
    logs = root / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    _write_json(logs / "hourly_autonomous_file_sim_latest.json", result)
    _write_json(logs / "hourly_deepseek_context_pack.json", result["deepseek_context_pack"])
    with (logs / "hourly_autonomous_file_sim.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
    (logs / "hourly_autonomous_file_sim.md").write_text(_render_markdown(result), encoding="utf-8")


def _highest_pressure_job(jobs: list[dict[str, Any]]) -> dict[str, Any]:
    return sorted(
        jobs,
        key=lambda job: (
            float(job.get("split_pressure") or 0),
            int(job.get("line_count") or 0),
            str(job.get("file") or ""),
        ),
        reverse=True,
    )[0]


def _relationship_graph_needs_learning(graph: dict[str, Any]) -> bool:
    edge_count = len(graph.get("edges") or [])
    node_count = len(graph.get("nodes") or [])
    return node_count > 0 and edge_count < max(4, node_count // 3)


def _registry_has_pressure(registry: dict[str, Any]) -> bool:
    summary = registry.get("summary") or {}
    return int(summary.get("critical") or 0) > 0 or int(summary.get("over_soft") or 0) > 0


def _related_files_for(target: str, sim: dict[str, Any]) -> list[str]:
    files: list[str] = []
    for edge in _edges_for(target, sim):
        if edge.get("from") == target and edge.get("to"):
            files.append(edge["to"])
        elif edge.get("to") == target and edge.get("from"):
            files.append(edge["from"])
    return _unique_strings(files)


def _edges_for(target: str, sim: dict[str, Any]) -> list[dict[str, Any]]:
    graph = sim.get("relationship_graph") or {}
    return [
        edge for edge in graph.get("edges") or []
        if edge.get("from") == target or edge.get("to") == target
    ]


def _validation_plan_for(root: Path, target: str, job: dict[str, Any]) -> list[str]:
    plan = list(job.get("validation_plan") or [])
    if plan:
        return _unique_strings(plan)
    path = Path(target)
    stem = path.stem
    candidates = [
        f"test_{stem}.py",
        f"test_{stem.replace('_seq', '')}.py",
        "test_file_self_sim_learning.py",
    ]
    existing = [candidate for candidate in candidates if (root / candidate).exists()]
    if existing:
        return [f"py -m pytest {existing[0]} -q"]
    return ["py -m py_compile src\\file_self_sim_learning_seq001_v001.py"]


def _existing_paths(root: Path, paths: list[str]) -> list[str]:
    return [
        path for path in _unique_strings(paths)
        if path and (root / path).exists()
    ]


def _intent_key(target: str, verb: str, target_state: str) -> str:
    scope = str(Path(target).parent).replace("\\", "/")
    stem = Path(target).stem if target else "unknown"
    if scope in {".", ""}:
        scope = "repo"
    return f"{scope}:{verb}:{stem}:{target_state}"


def _file_quote(file_name: str, quote: str) -> str:
    label = Path(file_name).name if file_name else "file"
    return f"{label}: \"{quote}\""


def _clean_intent(intent: str) -> str:
    return " ".join(str(intent or "").split())


def _stable_id(*parts: object) -> str:
    import hashlib

    raw = "::".join(str(part or "") for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _unique_strings(values: list[str]) -> list[str]:
    seen = set()
    out: list[str] = []
    for value in values:
        text = str(value or "").strip().replace("\\", "/")
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _main() -> int:
    parser = argparse.ArgumentParser(description="Run one hourly autonomous file-sim cycle.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--intent", default="", help="Operator intent seed for this hour.")
    parser.add_argument("--limit", type=int, default=8, help="Maximum file wake packets.")
    parser.add_argument("--run-validation", action="store_true", help="Run the selected safe validation plan.")
    parser.add_argument("--no-write", action="store_true", help="Do not write logs.")
    args = parser.parse_args()
    result = run_hourly_autonomous_file_sim(
        Path(args.root),
        args.intent,
        limit=args.limit,
        run_validation=args.run_validation,
        write=not args.no_write,
    )
    print(json.dumps({
        "schema": result["schema"],
        "intent_key": result["intent_key"],
        "action_type": result["selected_action"]["action_type"],
        "target_file": result["selected_action"]["target_file"],
        "next_hour_seed": result["next_hour_seed"]["debug_question"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
