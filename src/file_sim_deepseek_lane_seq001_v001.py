"""Per-sim DeepSeek maintenance lane.

Every file self-sim should emit one perpendicular DeepSeek job: compression,
split planning, validation mapping, or alternate-state simulation. Copilot stays
the foreground probe/orchestrator; DeepSeek keeps chewing safe maintenance work.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROMPT_JOBS = "logs/deepseek_prompt_jobs.jsonl"
CONTEXT_PACK = "logs/file_sim_deepseek_context_pack.json"


def queue_perpendicular_deepseek_job(root: Path, sim: dict[str, Any], *, write: bool = True) -> dict[str, Any]:
    """Queue exactly one DeepSeek job from a file-sim result."""
    root = Path(root)
    action = _select_action(sim)
    pack = _context_pack(sim, action)
    prompt = _prompt(sim, action)
    job_id = "dsfs-" + hashlib.sha1(
        f"{sim.get('ts')}|{action.get('mode')}|{action.get('target_file')}".encode("utf-8")
    ).hexdigest()[:16]
    job = {
        "schema": "deepseek_prompt_job/v1",
        "ts": _now(),
        "job_id": job_id,
        "status": "queued",
        "source": "file_sim_perpendicular_lane/v1",
        "mode": action["mode"],
        "model": os.environ.get("DEEPSEEK_CODING_MODEL") or os.environ.get("DEEPSEEK_MODEL") or "deepseek-v4-pro",
        "priority": action["priority"],
        "prompt": prompt,
        "focus_files": action["focus_files"],
        "context_pack_path": CONTEXT_PACK,
        "context_confidence": action["confidence"],
        "autonomous_write": False,
        "write_artifact": True,
        "artifact_path": f"logs/deepseek_artifacts/{job_id}_{action['mode']}.md",
        "max_tokens": 8000,
        "selected_action": action,
    }
    result = {
        "schema": "file_sim_deepseek_lane/v1",
        "ts": _now(),
        "queued": False,
        "job": job,
        "action": action,
        "context_pack_path": CONTEXT_PACK,
        "rule": "DeepSeek runs perpendicular to Copilot; it drafts plans/artifacts until approval opens surgery.",
    }
    if write:
        _write_json(root / CONTEXT_PACK, pack)
        _append_jsonl(root / PROMPT_JOBS, job)
        _write_json(root / "logs" / "file_sim_deepseek_lane_latest.json", result | {"queued": True})
        _append_jsonl(root / "logs" / "file_sim_deepseek_lane.jsonl", result | {"queued": True})
        result["queued"] = True
    return result


def _select_action(sim: dict[str, Any]) -> dict[str, Any]:
    ready = [job for job in sim.get("overcap_split_jobs") or [] if job.get("status") == "ready_for_split_plan"]
    blocked = [job for job in sim.get("overcap_split_jobs") or [] if str(job.get("status", "")).startswith("blocked")]
    if ready:
        job = _highest_pressure(ready)
        return _action("file_sim_split_plan", 1, job, "draft split/compression plan; no source overwrite")
    if blocked:
        job = _highest_pressure(blocked)
        return _action("file_sim_validation_map", 2, job, "find validation gate before split/compression")
    wake = (sim.get("wake_order") or [{}])[0]
    target = wake.get("file") or "src/MANIFEST.md"
    return {
        "mode": "file_sim_alternate_state",
        "priority": 3,
        "target_file": target,
        "intent_key": (sim.get("intent") or {}).get("intent_key", ""),
        "bounded_action": "simulate this file in a different architecture state; return risks, tests, and rewrite sketch only",
        "focus_files": _dedupe([target, "logs/file_self_sim_learning_latest.json", "logs/file_relationship_graph.json"]),
        "validation_plan": ["py -m pytest test_file_self_sim_learning.py -q"],
        "confidence": 0.35,
    }


def _action(mode: str, priority: int, job: dict[str, Any], bounded: str) -> dict[str, Any]:
    target = str(job.get("file") or "")
    focus = _dedupe([target, *(job.get("context_pack") or []), "src/MANIFEST.md", "MANIFEST.md"])
    return {
        "mode": mode,
        "priority": priority,
        "target_file": target,
        "intent_key": job.get("job_id") or "",
        "bounded_action": bounded,
        "focus_files": focus,
        "validation_plan": job.get("validation_plan") or [],
        "confidence": 0.75 if job.get("status") == "ready_for_split_plan" else 0.45,
        "line_count": job.get("line_count"),
        "size_state": job.get("size_state"),
        "split_pressure": job.get("split_pressure"),
    }


def _context_pack(sim: dict[str, Any], action: dict[str, Any]) -> dict[str, Any]:
    target = action.get("target_file")
    packets = [packet for packet in sim.get("learning_packets") or [] if packet.get("file") == target]
    edges = [
        edge for edge in (sim.get("relationship_graph") or {}).get("edges") or []
        if edge.get("from") == target or edge.get("to") == target
    ]
    return {
        "schema": "file_sim_deepseek_context_pack/v1",
        "ts": _now(),
        "role": "perpendicular_deepseek_lane",
        "target_state": "interlinked_source_state",
        "selected_action": action,
        "intent": sim.get("intent") or {},
        "learning_packets": packets[:2],
        "relationship_edges": edges[:16],
        "manifest_state": "folder MANIFEST.md is source-local state; root MANIFEST.md is global stage",
        "must_not_do": [
            "do not overwrite source",
            "do not split without validation",
            "do not erase manifest state",
            "do not outrank Copilot/operator approval",
        ],
    }


def _prompt(sim: dict[str, Any], action: dict[str, Any]) -> str:
    intent = sim.get("intent") or {}
    return "\n".join([
        "You are DeepSeek running perpendicular to Copilot inside the file-sim loop.",
        "Your job is continuous safe maintenance: compress, split-plan, map validation, or simulate an alternate codebase state.",
        "",
        f"INTENT_KEY: {intent.get('intent_key', '')}",
        f"TARGET_FILE: {action.get('target_file')}",
        f"MODE: {action.get('mode')}",
        f"BOUNDED_ACTION: {action.get('bounded_action')}",
        "",
        "CONTRACT:",
        "1. Return a concrete plan or surgical proposal artifact.",
        "2. Do not apply source changes.",
        "3. Name the exact context window and validation gates.",
        "4. Explain what backward learning should be stored in the folder manifest.",
        "5. Include an alternate-state simulation: what this file would look like after the rewrite, and what could break.",
    ])


def _highest_pressure(jobs: list[dict[str, Any]]) -> dict[str, Any]:
    return sorted(jobs, key=lambda row: (float(row.get("split_pressure") or 0), int(row.get("line_count") or 0)), reverse=True)[0]


def _dedupe(items: Any) -> list[str]:
    return list(dict.fromkeys(str(item) for item in items if item))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, sort_keys=True) + "\n")
