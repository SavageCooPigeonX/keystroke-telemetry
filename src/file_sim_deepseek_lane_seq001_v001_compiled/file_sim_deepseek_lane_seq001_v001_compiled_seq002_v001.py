"""file_sim_deepseek_lane_seq001_v001_compiled_seq002_v001.py — Auto-extracted by Pigeon Compiler."""
from .file_sim_deepseek_lane_seq001_v001_compiled_seq003_v001 import _action
from .file_sim_deepseek_lane_seq001_v001_compiled_seq004_v001 import _dedupe
from .file_sim_deepseek_lane_seq001_v001_compiled_seq004_v001 import _highest_pressure
from .file_sim_deepseek_lane_seq001_v001_compiled_seq004_v001 import _hush_blocks_mutation
from typing import Any
import json
import os

def _select_action(sim: dict[str, Any], hush: dict[str, Any] | None = None) -> dict[str, Any]:
    if _hush_blocks_mutation(hush):
        return _hush_blocked_action(sim, hush or {})
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


def _hush_blocked_action(sim: dict[str, Any], hush: dict[str, Any]) -> dict[str, Any]:
    repo = hush.get("repo_classification") or {}
    wake = (sim.get("wake_order") or [{}])[0]
    target = wake.get("file") or "logs/hush_intent_runtime_latest.json"
    return {
        "mode": "hush_mutation_fence_plan_only",
        "priority": 0,
        "target_file": target,
        "intent_key": (sim.get("intent") or {}).get("intent_key", ""),
        "bounded_action": "repo room is ambiguous; draft context plan only and do not propose source mutation",
        "focus_files": _dedupe([target, "logs/hush_intent_runtime_latest.json", "logs/file_self_sim_learning_latest.json"]),
        "validation_plan": ["review Hush repo classification", "ask operator for explicit repo lock"],
        "confidence": repo.get("repo_confidence", 0),
        "hush_reason": repo.get("reason", "Hush blocked mutation"),
    }
